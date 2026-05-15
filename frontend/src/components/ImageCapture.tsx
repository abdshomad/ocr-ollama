import { useCallback, useRef, useState } from "react";
import { useImage } from "../context/ImageContext";
import { useCamera } from "../hooks/useCamera";

const ACCEPT = "image/jpeg,image/png,image/webp,image/gif";

export function ImageCapture() {
  const { file, previewUrl, setImage, clearImage } = useImage();
  const { videoRef, active, error: camError, start, stop, capture } = useCamera();
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  const onFile = useCallback(
    (f: File | null) => {
      if (!f) return;
      setImage(f);
      if (active) stop();
    },
    [setImage, active, stop]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDrag(false);
      const f = e.dataTransfer.files[0];
      if (f?.type.startsWith("image/")) onFile(f);
    },
    [onFile]
  );

  const onCapture = () => {
    const shot = capture();
    if (shot) {
      onFile(shot);
      stop();
    }
  };

  return (
    <section className="card">
      <h2>Image</h2>
      {!file ? (
        <>
          <div
            className={`dropzone${drag ? " dragover" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
          >
            <p>Drop an image here or click to upload</p>
            <p className="muted">JPEG, PNG, WebP, GIF — max 10 MB</p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            hidden
            onChange={(e) => onFile(e.target.files?.[0] ?? null)}
          />
          <div className="camera-box" style={{ marginTop: "1rem" }}>
            {!active ? (
              <button type="button" onClick={start}>
                Open camera
              </button>
            ) : (
              <>
                <video ref={videoRef} playsInline muted />
                <div className="row" style={{ marginTop: "0.5rem" }}>
                  <button type="button" className="primary" onClick={onCapture}>
                    Capture
                  </button>
                  <button type="button" onClick={stop}>
                    Close camera
                  </button>
                </div>
              </>
            )}
            {camError && <p className="health-bad">{camError}</p>}
          </div>
        </>
      ) : (
        <>
          <img src={previewUrl ?? ""} alt="Selected" className="preview-img" />
          <p className="muted">{file.name}</p>
          <div className="row" style={{ marginTop: "0.5rem" }}>
            <button type="button" onClick={() => inputRef.current?.click()}>
              Replace
            </button>
            <button type="button" onClick={clearImage}>
              Clear
            </button>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            hidden
            onChange={(e) => onFile(e.target.files?.[0] ?? null)}
          />
        </>
      )}
    </section>
  );
}
