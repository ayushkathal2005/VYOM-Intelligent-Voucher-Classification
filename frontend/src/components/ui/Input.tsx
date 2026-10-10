"use client";

import React, { forwardRef } from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className = "", id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs uppercase tracking-wider font-semibold text-[#A69A87]"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`w-full px-4 py-3 bg-[#11100E] border border-[rgba(191,145,51,0.2)] text-[#F4EBDD] placeholder-[#A69A87]/50 rounded-sm text-sm focus:border-[#F0AE2C] focus:bg-[#0B0805] focus:outline-none transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${
            error ? "border-red-500/80 focus:border-red-500" : ""
          } ${className}`}
          {...props}
        />
        {hint && !error && (
          <span className="text-xs text-[#A69A87]/70">{hint}</span>
        )}
        {error && (
          <span className="text-xs text-red-400 font-medium" role="alert">
            {error}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
