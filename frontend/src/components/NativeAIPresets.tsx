import type { ReactNode } from 'react';

export type NativePreset = {
  label: string;
  apply: () => void;
};

export default function NativeAIPresets({
  presets,
  disabled = false,
  note = 'Each example fills every required and optional field. Review values before running.',
}: {
  presets: NativePreset[];
  disabled?: boolean;
  note?: ReactNode;
}) {
  return (
    <div className="ai-preset-bar" data-testid="native-ai-presets">
      <div>
        <strong>Complete examples</strong>
        <p>{note}</p>
      </div>
      <div className="ai-actions">
        {presets.map((preset) => (
          <button
            key={preset.label}
            type="button"
            className="btn btn-secondary"
            disabled={disabled}
            onClick={preset.apply}
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}
