# Local steps: Codex image generation on the Windows PC

For a Claude Code session running on the user's Windows PC, in `D:\work\sweet-shoe-atelie`.
Do these in order and report each result. Use `cmd` quoting (double quotes).

1. If this folder has no git repository yet, clone the project into it:
   `git clone -b claude/game-art-defects-aesthetics-hre0nm https://github.com/pu873967671-code/sweet-shoe-atelier.git .`
   (If the folder is not empty and has no repository, clone into a subfolder instead and work there.)
2. Run `codex.cmd login status`. It must show a ChatGPT login. If not, stop and tell the user.
3. In the project folder run:

   ```
   codex.cmd exec --sandbox workspace-write "Use the built-in $imagegen image generator to create a product shot of retro sneakers, with an off-white background and soft studio lighting. Save the final PNG to assets/imagegen-test.png in the current project. Do not call the OpenAI image API."
   ```

4. Check that `assets/imagegen-test.png` exists and report its full path.
5. Only if it exists, add this section to `CLAUDE.md` in the project folder (create the file if needed):

   ```markdown
   ## Generating images with Codex
   When the user says "generate an image with Codex", run Codex CLI's built-in image
   generator from the project folder (it uses the ChatGPT login, not an API key):

       codex.cmd login status
       codex.cmd exec --sandbox workspace-write "Use the built-in $imagegen image generator to create <description>. Save the final PNG to <path inside this project>. Do not call the OpenAI image API."

   Then confirm the file exists and report its full path.
   ```

6. Do not commit or push anything yet. Report back the image path (or the exact error).
