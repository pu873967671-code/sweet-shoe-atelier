## Generating images with Codex
When the user says "generate an image with Codex", run Codex CLI's built-in image
generator from the project folder (it uses the ChatGPT login, not an API key):

    codex.cmd login status
    codex.cmd exec -m gpt-6.1-terra --sandbox workspace-write "Use the built-in $imagegen image generator to create <description>. Save the final PNG to <path inside this project>. Do not call the OpenAI image API."

Then confirm the file exists and report its full path.
