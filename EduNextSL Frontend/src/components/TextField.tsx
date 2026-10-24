type TextFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "email";
  autoComplete?: string;
  error?: string;
  name?: string;
};

export function TextField({
  label,
  value,
  onChange,
  type = "text",
  autoComplete,
  error,
  name,
}: TextFieldProps) {
  return (
    <div className="field-block">
      <label className="auth-field" aria-label={label}>
        <input
          name={name}
          type={type}
          placeholder={label}
          value={value}
          autoComplete={autoComplete}
          aria-invalid={error ? true : undefined}
          onChange={(event) => onChange(event.target.value)}
        />
      </label>
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
