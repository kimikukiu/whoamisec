const http = require('http');
const ZAI = require('z-ai-web-dev-sdk').default;

const PORT = 20127;
let zai = null;

async function init() {
    zai = await ZAI.create();
    console.log('Z-AI Proxy ready on port ' + PORT);
}

const MODELS = [
    "z-ai/glm-4-plus", "z-ai/glm-4-flash", "z-ai/glm-z1-air",
    "z-ai/claude-sonnet-4", "z-ai/claude-haiku-4", "z-ai/gpt-4o",
    "z-ai/gpt-4o-mini", "z-ai/deepseek-chat", "z-ai/gemini-2.5-pro",
    "z-ai/gemini-2.0-flash", "z-ai/qwen-max", "z-ai/mistral-large",
    "z-ai/default"
];

const server = http.createServer(async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') { res.writeHead(200); res.end(); return; }

    if (req.method === 'GET' && req.url === '/v1/models') {
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify({
            object: "list",
            data: MODELS.map(m => ({id: m, object: "model", owned_by: "z-ai-free"}))
        }));
        return;
    }

    if (req.method === 'POST' && (req.url === '/v1/chat/completions' || req.url === '/chat/completions')) {
        let body = '';
        req.on('data', c => body += c);
        req.on('end', async () => {
            try {
                const data = JSON.parse(body);
                const messages = data.messages || [];
                const maxTokens = data.max_tokens || 2000;
                const stream = data.stream || false;

                if (!zai) await init();

                const completion = await zai.chat.completions.create({
                    messages,
                    max_tokens: maxTokens,
                    temperature: data.temperature || 0.7,
                });

                if (completion.choices && completion.choices[0]) {
                    const content = completion.choices[0].message.content;
                    if (stream) {
                        res.writeHead(200, {'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive'});
                        for (let i = 0; i < content.length; i += 20) {
                            const chunk = content.substring(i, i + 20);
                            res.write('data: ' + JSON.stringify({id:"zai_"+Date.now(),object:"chat.completion.chunk",choices:[{index:0,delta:{content:chunk},finish_reason:null}]}) + '\n\n');
                        }
                        res.write('data: ' + JSON.stringify({choices:[{delta:{},finish_reason:"stop"}]}) + '\n\n');
                        res.write('data: [DONE]\n\n');
                        res.end();
                    } else {
                        res.writeHead(200, {'Content-Type': 'application/json'});
                        res.end(JSON.stringify({
                            id: "zai_" + Date.now(),
                            object: "chat.completion",
                            choices: [{index: 0, message: {role: "assistant", content: content}, finish_reason: "stop"}],
                            model: completion.model || "z-ai-default",
                            usage: completion.usage || {prompt_tokens: 0, completion_tokens: 0, total_tokens: 0}
                        }));
                    }
                } else {
                    res.writeHead(500, {'Content-Type': 'application/json'});
                    res.end(JSON.stringify({error: {message: "No response from Z-AI SDK"}}));
                }
            } catch (e) {
                res.writeHead(500, {'Content-Type': 'application/json'});
                res.end(JSON.stringify({error: {message: e.message}}));
            }
        });
        return;
    }

    res.writeHead(404);
    res.end('Not Found');
});

init();
server.listen(PORT, '0.0.0.0');
