"use client";

import React, { useState, useEffect } from "react";

interface SchemaFormProps {
  schema?: Record<string, unknown>;
  onSubmit: (values: Record<string, unknown>) => void;
  isLoading?: boolean;
}

export function SchemaForm({ schema, onSubmit, isLoading }: SchemaFormProps) {
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});
  const [jsonFallback, setJsonFallback] = useState<string>("{}");
  const [useRawJson, setUseRawJson] = useState(false);
  const [parseError, setParseError] = useState("");

  const properties = (schema?.properties as Record<string, Record<string, unknown>>) || {};
  const requiredFields = (schema?.required as string[]) || [];

  useEffect(() => {
    // Reset form values on tool change
    setFormValues({});
    setJsonFallback("{}");
    setParseError("");
  }, [schema]);

  const handleChange = (key: string, value: unknown) => {
    setFormValues((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setParseError("");

    if (useRawJson) {
      try {
        const parsed = JSON.parse(jsonFallback);
        onSubmit(parsed);
      } catch (err: unknown) {
        const error = err as Error;
        setParseError(`JSON parse error: ${error.message}`);
      }
      return;
    }

    onSubmit(formValues);
  };

  const propKeys = Object.keys(properties);

  return (
    <form onSubmit={handleFormSubmit} className="space-y-4">
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
        <span className="text-xs font-semibold text-[var(--text)] uppercase tracking-wider">
          Parameters ({propKeys.length})
        </span>
        <button
          type="button"
          onClick={() => {
            if (!useRawJson) {
              setJsonFallback(JSON.stringify(formValues, null, 2));
            }
            setUseRawJson(!useRawJson);
          }}
          className="text-[11px] text-[var(--accent)] hover:underline cursor-pointer"
        >
          {useRawJson ? "Switch to Form Mode" : "Switch to Raw JSON"}
        </button>
      </div>

      {parseError && (
        <div className="p-2.5 rounded bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-xs text-[var(--danger)]">
          {parseError}
        </div>
      )}

      {useRawJson ? (
        <div>
          <textarea
            rows={8}
            value={jsonFallback}
            onChange={(e) => setJsonFallback(e.target.value)}
            className="w-full px-3 py-2 text-xs font-mono rounded bg-[var(--surface)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
          />
        </div>
      ) : propKeys.length === 0 ? (
        <p className="text-xs text-[var(--text-muted)] italic">
          This tool takes no arguments.
        </p>
      ) : (
        <div className="space-y-3">
          {propKeys.map((key) => {
            const prop = properties[key] || {};
            const isRequired = requiredFields.includes(key);
            const propType = typeof prop.type === "string" ? prop.type : "string";
            const description = typeof prop.description === "string" ? prop.description : null;
            const enumOptions = Array.isArray(prop.enum) ? (prop.enum as string[]) : null;
            const val = formValues[key];

            return (
              <div key={key} className="space-y-1">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-mono font-medium text-[var(--text)]">
                    {key}
                    {isRequired && <span className="text-[var(--danger)] ml-0.5">*</span>}
                  </label>
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase">
                    {propType}
                  </span>
                </div>

                {description && (
                  <p className="text-[11px] text-[var(--text-muted)] leading-tight">
                    {description}
                  </p>
                )}

                {propType === "boolean" ? (
                  <select
                    value={val !== undefined ? String(val) : ""}
                    onChange={(e) =>
                      handleChange(
                        key,
                        e.target.value === "" ? undefined : e.target.value === "true"
                      )
                    }
                    className="w-full px-2.5 py-1.5 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none"
                  >
                    <option value="">(Select boolean)</option>
                    <option value="true">true</option>
                    <option value="false">false</option>
                  </select>
                ) : enumOptions ? (
                  <select
                    value={String(val || "")}
                    onChange={(e) => handleChange(key, e.target.value || undefined)}
                    className="w-full px-2.5 py-1.5 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none"
                  >
                    <option value="">(Select option)</option>
                    {enumOptions.map((opt: string) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                ) : propType === "integer" || propType === "number" ? (
                  <input
                    type="number"
                    value={val !== undefined ? String(val) : ""}
                    onChange={(e) =>
                      handleChange(
                        key,
                        e.target.value === "" ? undefined : Number(e.target.value)
                      )
                    }
                    className="w-full px-2.5 py-1.5 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                  />
                ) : (
                  <input
                    type="text"
                    value={String(val || "")}
                    onChange={(e) => handleChange(key, e.target.value)}
                    required={isRequired}
                    placeholder={`Enter ${key}`}
                    className="w-full px-2.5 py-1.5 text-xs rounded bg-[var(--surface-raised)] border border-[var(--border)] text-[var(--text)] focus:outline-none focus:border-[var(--accent)]"
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="pt-2">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-2 px-4 rounded bg-[var(--accent)] text-white text-xs font-semibold hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50 cursor-pointer"
        >
          {isLoading ? "Running Tool..." : "Run Tool"}
        </button>
      </div>
    </form>
  );
}
