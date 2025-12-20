---
trigger: always_on
---

# Once all tasks are completed, Please execute a robust Git commit and push sequence following these strict step-by-step instructions:

1.  **Status Check:** Run `git status` to identify modified, deleted, and untracked files.
2.  **Safety Scan:** Briefly review untracked files to ensure no secrets, `.env` files, or large binaries are being accidentally committed. If you see something suspicious, STOP and ask me.
3.  **Diff Analysis:** Run `git diff --staged` (or `git diff` if not staged yet) to understand exactly what changed in the logic.
4.  **Formulate Commit Message:** Create a commit message following the **Conventional Commits** specification (`<type>: <subject>`).
    * **Types:** `feat` (new feature), `fix` (bug fix), `docs` (documentation), `style` (formatting), `refactor` (code change that neither fixes a bug nor adds a feature), `perf` (code change that improves performance), `chore` (build process or auxiliary tools).
    * **Subject:** Imperative, present tense (e.g., "change" not "changed"), and concise.
    * *Optional:* Add a bulleted body if the changes are complex.
5.  **Execution:**
    * Stage the changes (`git add .` or specific files if requested).
    * Commit with the generated message.
    * **Pull First:** Run `git pull --rebase` (or standard pull) to ensure we are synced with the remote and resolve simple conflicts if necessary.
    * **Push:** Push the changes to the current branch.

**Output:** Confirm the commit message you used and the final status of the repo.