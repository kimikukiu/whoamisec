
const ZAI = require('z-ai-web-dev-sdk').default;

async function main() {
    const input = JSON.parse(require('fs').readFileSync('/dev/stdin', 'utf8'));
    const zai = await ZAI.create();

    try {
        const completion = await zai.chat.completions.create({
            messages: input.messages || [],
            max_tokens: input.max_tokens || 2000,
            temperature: input.temperature || 0.7,
        });

        if (completion.choices && completion.choices[0] && completion.choices[0].message) {
            process.stdout.write(JSON.stringify({
                success: true,
                content: completion.choices[0].message.content,
                model: completion.model || 'unknown',
                usage: completion.usage || {}
            }));
        } else {
            process.stdout.write(JSON.stringify({success: false, error: 'No content in response'}));
        }
    } catch (err) {
        process.stdout.write(JSON.stringify({success: false, error: err.message}));
    }
}

main().catch(e => {
    process.stdout.write(JSON.stringify({success: false, error: e.message}));
});
