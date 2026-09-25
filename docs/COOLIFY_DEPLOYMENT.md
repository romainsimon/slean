# Slean Coolify deployment candidate

This describes the required configuration for the existing `slean.org` application (`iegozztocwpvv1xzodzynpec`). The source is `romainsimon/slean`, branch `main`, base directory `/`, and domain `https://slean.org`.

After the reviewed PR stack is assembled into one exact candidate, the final image is tested, and a recovery image is retained, check these application fields before merging to `main`:

```json
{
  "build_pack": "dockerfile",
  "dockerfile_location": "/Dockerfile",
  "ports_exposes": "80",
  "include_source_commit_in_build": true,
  "inject_build_args_to_dockerfile": false,
  "health_check_enabled": true,
  "health_check_path": "/",
  "health_check_port": "80",
  "docker_images_to_keep": 2
}
```

Every image build requires `SOURCE_COMMIT` as a full, lowercase 40-character Git SHA. The builder stamps that exact value into `build-info.json` and the OCI revision label. When the build context contains Git metadata, it compares the value with `HEAD` and rejects a dirty checkout. Coolify may provide a source archive without `.git`; in that case the builder cannot compare the archive with a Git object or inspect its cleanliness. It records `source_tree_clean: null` (unknown), never `true`, and relies on Coolify's injected commit to identify the archive. This provenance does not independently prove that the archive contents hash to that commit.

The final Nginx image listens on port 80 and checks `/` and `/en/` from inside the container. Keep the existing domain and automatic deployment behavior. Do not add a separate build or start command.

Before a first deployment, retain a tested image and its compatible application settings as a recovery path. At the time this file was written, the existing Slean container had never become healthy, so it cannot serve as a rollback image. Test the final image for the exact release SHA in CI when the workflow is available, or locally when GitHub Actions is unavailable. A successful source build or HTTP preview does not prove the final image.

Run the read-only portfolio audit and the exact candidate check before changing the live application:

```sh
node /Users/romainsimon/dev/ceo/scripts/release-preflight.mjs audit
node /Users/romainsimon/dev/ceo/scripts/release-preflight.mjs check \
  --app iegozztocwpvv1xzodzynpec \
  --repo romainsimon/slean \
  --sha <exact-reviewed-sha> \
  --runtime-check final-image
```

After a deployment, compare the running image revision label and `/build-info.json` with the released SHA, verify `/`, `/en/`, `/portes-et-ou/`, `/en/and-or-gates/`, `/find/`, and `/en/find/`, and confirm one real Plausible pageview for `slean.org`. A local preview cannot verify analytics ingestion.
