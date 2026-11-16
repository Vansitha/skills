# Google sign-in client

The uploader posts to YouTube through the YouTube Data API, using a small
Google Cloud project that belongs to the user. It costs nothing (YouTube allows
100 uploads a day per project). This takes about 10 minutes, once.

Walk the user through it one part at a time: they click in their own browser,
signed in with the Google account that owns their YouTube channel. Check first
that the channel exists (youtube.com, profile picture, *Create a channel*).

Every link opens the right page. Pages look empty when no project is selected,
so the project name at the top left must say `clips-uploader`; if it doesn't,
they click it and pick that project.

## A. Make a project and turn on the YouTube API

1. <https://console.cloud.google.com/projectcreate>: Project name
   `clips-uploader`, click **Create**, wait a few seconds.
2. <https://console.cloud.google.com/apis/library/youtube.googleapis.com>:
   click **Enable**.

## B. Set up the sign-in screen

3. <https://console.cloud.google.com/auth/branding>: it says *Google Auth
   platform not configured yet*, which is expected. Click **Get started**:
   - **App Information**: App name `Clips uploader`, User support email: theirs.
     **Next**.
   - **Audience**: **External**. **Next**.
   - **Contact Information**: their email. **Next**.
   - **Finish**: tick the agreement, **Continue**, then **Create**.
4. <https://console.cloud.google.com/auth/audience>: Publishing status says
   *Testing*. Click **Publish app**, then **Confirm**, so it says
   **In production**. In Testing, Google signs them out every 7 days and
   uploads stop until `/clips auth`. Publishing doesn't need Google's review
   for their own use; Google shows an "unverified app" warning at sign-in
   instead.

   If they'd rather stay in Testing: under **Test users** click **Add users**
   and add their own Gmail address. Without that, sign-in fails with "Access
   blocked".

## C. Make the key file

5. <https://console.cloud.google.com/auth/clients>: **Create client**,
   Application type **Desktop app**, Name `clips`, **Create**.
6. In the window that opens, click **Download JSON** before closing it. The
   file lands in Downloads as `client_secret_….json`. Leave it there and run
   `setup` again: it moves the file into `~/.config/clips/youtube/`. (If they
   closed the window, they click the client in the list and download it there.)

## D. Sign in

Run `auth` in a terminal the user can see. Their browser opens:

- Pick the Google account, then **the channel** the clips should go to (a brand
  channel shows up as its own entry).
- On *Google hasn't verified this app*: **Advanced**, then **Go to Clips
  uploader (unsafe)**. It's their own app. Then **Continue** and allow access.
- The terminal prints the channel name it will upload to.

## When it goes wrong

- *Access blocked: … has not completed the Google verification process*: the
  app is still in Testing and the account isn't a test user. Do step 4.
- *The account you picked has no YouTube channel*: create the channel, then run
  `auth` again.
- Empty console pages: the wrong project (or none) is selected.
- `setup` says the Downloads file is a *Web application* client: make another
  client with type **Desktop app** (step 5).

`client_secret.json` and `token.json` in `~/.config/clips/youtube/` are
private: never share them or put them in a repository. To sign out, delete
`token.json`.
