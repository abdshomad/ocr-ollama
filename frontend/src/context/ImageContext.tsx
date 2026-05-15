import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

interface ImageContextValue {
  file: File | null;
  previewUrl: string | null;
  setImage: (file: File | null) => void;
  clearImage: () => void;
}

const ImageContext = createContext<ImageContextValue | null>(null);

export function ImageProvider({ children }: { children: ReactNode }) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const setImage = useCallback((next: File | null) => {
    setPreviewUrl((prevUrl) => {
      if (prevUrl) URL.revokeObjectURL(prevUrl);
      return next ? URL.createObjectURL(next) : null;
    });
    setFile(next);
  }, []);

  const clearImage = useCallback(() => setImage(null), [setImage]);

  const value = useMemo(
    () => ({ file, previewUrl, setImage, clearImage }),
    [file, previewUrl, setImage, clearImage]
  );

  return <ImageContext.Provider value={value}>{children}</ImageContext.Provider>;
}

export function useImage() {
  const ctx = useContext(ImageContext);
  if (!ctx) throw new Error("useImage must be used within ImageProvider");
  return ctx;
}
