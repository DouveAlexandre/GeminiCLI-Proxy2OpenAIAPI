/* ------------------------------------------------------------------ */
/*  mapper.ts – OpenAI ⇆ Gemini (with reasoning/1 M context)           */
/* ------------------------------------------------------------------ */
import { fetchAndEncode } from './remoteimage';
import { z } from 'zod';
import { ToolRegistry } from '@google/gemini-cli-core/dist/src/tools/tool-registry.js';
import { getModel } from './chatwrapper';

/* ------------------------------------------------------------------ */
type Part = { text?: string; inlineData?: { mimeType: string; data: string } };

/* ------------------------------------------------------------------ */
async function callLocalFunction(_name: string, _args: unknown) {
  return { ok: true };
}

/* ================================================================== */
/* Request mapper: OpenAI ➞ Gemini                                     */
/* ================================================================== */
export async function mapRequest(body: any) {
  const parts: Part[] = [];

  /* ---- convert messages & vision --------------------------------- */
  for (const m of body.messages) {
    if (Array.isArray(m.content)) {
      for (const item of m.content) {
        if (item.type === 'image_url') {
          parts.push({ inlineData: await fetchAndEncode(item.image_url.url) });
        } else if (item.type === 'text') {
          parts.push({ text: item.text });
        }
      }
    } else {
      parts.push({ text: m.content });
    }
  }

  /* ---- base generationConfig ------------------------------------- */
  const generationConfig: Record<string, unknown> = {
    temperature: body.temperature,
    maxOutputTokens: body.max_tokens,
    topP: body.top_p,
    ...(body.generationConfig ?? {}), // copy anything ST already merged
  };
  if (body.include_reasoning === true) {
    generationConfig.enable_thoughts = true;        // ← current flag
    generationConfig.thinking_budget ??= 2048;      // optional limit
  }

  /* ---- auto-enable reasoning & 1 M context ----------------------- */
  if (body.include_reasoning === true && generationConfig.thinking !== true) {
    generationConfig.thinking = true;
    generationConfig.thinking_budget ??= 2048;
  }
  generationConfig.maxInputTokens ??= 1_000_000; // lift context cap

  const geminiReq = {
    contents: [{ role: 'user', parts }],
    generationConfig,
    stream: body.stream,
  };

  console.log('Gemini request:', geminiReq);

  /* ---- Tool / function mapping ----------------------------------- */
  const tools = new ToolRegistry({} as any);

  if (body.functions?.length) {
    const reg = tools as any;
    body.functions.forEach((fn: any) =>
      reg.registerTool(
        fn.name,
        {
          title: fn.name,
          description: fn.description ?? '',
          inputSchema: z.object(fn.parameters?.properties ?? {}),
        },
        async (args: unknown) => callLocalFunction(fn.name, args),
      ),
    );
  }

  return { geminiReq, tools };
}

/* ================================================================== */
/* Non-stream response: Gemini ➞ OpenAI                                */
/* ================================================================== */
export function mapResponse(gResp: any) {
  const usage = gResp.usageMetadata ?? {};
  const hasError = typeof gResp.candidates === 'undefined';

  console.log('Received response:', gResp);

  if (hasError) {
    console.error('No candidates returned.');

    return {
      error: {
        message: gResp?.promptFeedback?.blockReason ?? 'No candidates returned.',
      }
    }
  }
  
  // Extract content from the response structure
  let content = '';
  if (gResp.text) {
    content = gResp.text;
  } else if (gResp.candidates && gResp.candidates[0]) {
    const candidate = gResp.candidates[0];
    if (candidate.content && candidate.content.parts) {
      // Concatenate all text parts
      content = candidate.content.parts
        .filter((part: any) => part.text)
        .map((part: any) => part.text)
        .join('');
    } else if (candidate.text) {
      content = candidate.text;
    }
  }
  
  return {
    id: `chatcmpl-${Date.now()}`,
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: getModel(),
    choices: [
      {
        index: 0,
        message: { role: 'assistant', content: content },
        finish_reason: 'stop',
      },
    ],
    usage: {
      prompt_tokens: usage.promptTokens ?? 0,
      completion_tokens: usage.candidatesTokens ?? 0,
      total_tokens: usage.totalTokens ?? 0,
    },
  };
}

/* ================================================================== */
/* Stream chunk mapper: Gemini ➞ OpenAI                                */
/* ================================================================== */

export function mapStreamChunk(chunk: any) {
  const part = chunk?.candidates?.[0]?.content?.parts?.[0] ?? {};
  const delta: any = { role: 'assistant' };

  if (part.thought === true) {
    delta.content = `<think>${part.text ?? ''}`;  // ST renders grey bubble
  } else if (typeof part.text === 'string') {
    delta.content = part.text;
  }
  return { choices: [ { delta, index: 0 } ] };
}


