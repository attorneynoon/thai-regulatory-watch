# Maintain from the cloud

The scheduler is GitHub Actions; it keeps running independently of a chat session or laptop. ChatGPT can analyze retrieved RSS/JSON. Code maintenance uses a GitHub-capable cloud coding environment.

1. Open Codex cloud using the intended ChatGPT account.
2. Connect GitHub and grant the application access to `attorneynoon/thai-regulatory-watch`.
3. Create an environment selecting this repository. Using Python 3.12, set up with `python -m pip install --upgrade pip==26.2.1` and then `python -m pip install -r requirements.txt`.
4. Allow the official source hosts only when a task needs live collection. Offline parser tests/builds need no runtime network.
5. Ask for changes on a branch and review the resulting PR. The root `AGENTS.md` states invariants and verification commands.

Examples:

- “Add this official government URL as a pending source; prepare its source fixture, selectors and tests in a PR.”
- “Inspect source health and repair the ETDA adapter using permitted access. Preserve published history and report what was live-verified.”
- “Read the changes JSON and produce review-only GRC intake with exact source IDs and provenance.”

GitHub connector visibility and Codex cloud environment access are separate from the local CLI login. Account/app installation and cloud-environment setup may require the owner to finish interactive authorization. Do not paste access tokens into chat. A public repository does not by itself guarantee that a particular ChatGPT tool can edit it.

Official references: [Codex cloud setup](https://learn.chatgpt.com/docs/cloud), [GitHub integration](https://learn.chatgpt.com/docs/third-party/github), [GitHub custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
