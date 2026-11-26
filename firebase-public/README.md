Intentionally empty.

Firebase Hosting requires a `public` directory, but every request to this site
is rewritten to the Cloud Run service (see `firebase.json`). Static files are
matched BEFORE rewrites, so anything placed here -- an `index.html` above all
-- would shadow the app and be served instead of it.
