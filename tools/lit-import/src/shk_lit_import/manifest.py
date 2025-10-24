import json, pathlib, zipfile

def bundle(in_dir: str, out_dir: str):
    in_path = pathlib.Path(in_dir)
    out_path = pathlib.Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    zipf = out_path / "shk-lit-bundle.zip"
    with zipfile.ZipFile(zipf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for fp in in_path.rglob("*"):
            if fp.is_file():
                z.write(fp, fp.relative_to(in_path))
    manifest = {"inputs": str(in_path), "bundle": str(zipf.name)}
    (out_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[release-bundle] Wrote {zipf} and manifest.json")
