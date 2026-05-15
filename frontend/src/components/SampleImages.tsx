import { useCallback, useEffect, useState } from "react";
import { fetchSampleImage, getSamples, sampleImageUrl } from "../api/client";
import { useImage } from "../context/ImageContext";
import type { SampleImage } from "../types";

export function SampleImages() {
  const { file, setImage } = useImage();
  const [samples, setSamples] = useState<SampleImage[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [picking, setPicking] = useState<string | null>(null);

  useEffect(() => {
    getSamples()
      .then((list) => {
        setSamples(list);
        setLoadError(null);
      })
      .catch((e) => {
        setSamples([]);
        setLoadError(e instanceof Error ? e.message : "Could not load samples");
      });
  }, []);

  const onPick = useCallback(
    async (sample: SampleImage) => {
      setPicking(sample.name);
      setLoadError(null);
      try {
        const blob = await fetchSampleImage(sample.name);
        const type = blob.type || "image/jpeg";
        setImage(new File([blob], sample.name, { type }));
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : "Failed to load sample");
      } finally {
        setPicking(null);
      }
    },
    [setImage]
  );

  if (!samples.length && !loadError) return null;

  return (
    <div className="sample-images">
      <p className="muted sample-images-title">Sample images — click to load</p>
      {loadError && <p className="health-bad">{loadError}</p>}
      <div className="sample-grid">
        {samples.map((sample) => {
          const active = file?.name === sample.name;
          const busy = picking === sample.name;
          return (
            <button
              key={sample.name}
              type="button"
              className={`sample-thumb${active ? " sample-thumb-active" : ""}`}
              disabled={busy}
              onClick={() => onPick(sample)}
              title={sample.label}
              aria-label={`Load sample image ${sample.label}`}
              aria-pressed={active}
            >
              <img src={sampleImageUrl(sample.name)} alt="" loading="lazy" />
              <span className="sample-thumb-label" aria-hidden>
                {sample.label}
              </span>
              {busy && <span className="sample-thumb-busy">Loading…</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
