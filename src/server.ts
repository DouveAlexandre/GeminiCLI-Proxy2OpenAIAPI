import 'dotenv/config';
import http from 'http';
import { sendChat, sendChatStream, listModels } from './chatwrapper';
import { mapRequest, mapResponse, mapStreamChunk } from './mapper';

/* ── basic config ─────────────────────────────────────────────────── */
const PORT = Number(process.env.PORT ?? 11434);

/* ── CORS helper ──────────────────────────────────────────────────── */
function allowCors(res: http.ServerResponse) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
}

/* ── JSON body helper ─────────────────────────────────────────────── */
function readJSON(
  req: http.IncomingMessage,
  res: http.ServerResponse,
): Promise<any | null> {
  return new Promise((resolve) => {
    let data = '';
    req.on('data', (c) => (data += c));
    req.on('end', () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch {
        res.writeHead(400).end(); // malformed JSON
        resolve(null);
      }
    });
  });
}

/* ── server ───────────────────────────────────────────────────────── */
http
  .createServer(async (req, res) => {
    allowCors(res);

    console.log('➜', req.method, req.url);

    /* -------- pre-flight ---------- */
    if (req.method === 'OPTIONS') {
      res.writeHead(204).end();
      return;
    }

    /* -------- /v1/models ---------- */
    if (req.url === '/v1/models') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          data: listModels(),
        }),
      );
      return;
    }

    /* ---- /v1/chat/completions ---- */
    if (req.url === '/v1/chat/completions' && req.method === 'POST') {
      const body = await readJSON(req, res);
      if (!body) {
        return; // readJSON already handled the response
      }

      try {
        const { geminiReq, tools } = await mapRequest(body);

        if (body.stream) {
          // Check if headers were already sent
          if (!res.headersSent) {
            res.writeHead(200, {
              'Content-Type': 'text/event-stream',
              'Cache-Control': 'no-cache',
              Connection: 'keep-alive',
            });
          }

          console.log('➜ sending HTTP 200 streamed response');

          try {
            for await (const chunk of sendChatStream({ ...geminiReq, tools })) {
              if (!res.destroyed) {
                res.write(`data: ${JSON.stringify(mapStreamChunk(chunk))}\n\n`);
              }
            }
            if (!res.destroyed) {
              res.end('data: [DONE]\n\n');
            }
          } catch (streamErr: any) {
            console.error('Streaming error:', streamErr);
            if (!res.destroyed && !res.headersSent) {
              res.writeHead(500, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: { message: streamErr.message } }));
            }
          }

          console.log('➜ done sending streamed response');
        } else {
          const gResp = await sendChat({ ...geminiReq, tools });
          const mapped = mapResponse(gResp);
          const code = 200;
          
          if (!res.headersSent) {
            res.writeHead(code, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(mapped));
          }

          console.log('✅ Replied HTTP ' + code + ' response', mapped);
        }
      } catch (err: any) {
        console.error('HTTP 500 Proxy error ➜', err);
        if (!res.headersSent) {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: { message: err.message } }));
        }
      }

      return;
    }

    console.log('➜ unknown request, returning HTTP 404');
    /* ---- anything else ---------- */
    res.writeHead(404).end();
  })
  .listen(PORT, () => console.log(`OpenAI proxy listening on http://localhost:${PORT}`));
