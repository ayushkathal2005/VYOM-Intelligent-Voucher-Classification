"use client";

import React, { forwardRef } from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "gold" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className = "",
      variant = "gold",
      size = "md",
      isLoading = false,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "relative inline-flex items-center justify-center font-medium transition-all duration-200 select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-[#F0AE2C] focus-visible:outline-offset-2";

    const sizeStyles = {
      sm: "px-3.5 py-1.5 text-xs rounded-sm tracking-wider uppercase",
      md: "px-6 py-3 text-sm rounded-sm tracking-wide",
      lg: "px-8 py-4 text-base rounded-sm tracking-wide",
    };

    const variantStyles = {
      gold: "bg-[#F0AE2C] hover:bg-[#d89920] text-[#050505] font-semibold shadow-lg shadow-[#F0AE2C]/10 active:scale-[0.99]",
      secondary:
        "bg-[#11100E] hover:bg-[#1a1814] text-[#F4EBDD] border border-[rgba(191,145,51,0.2)] hover:border-[#F0AE2C]/40",
      outline:
        "bg-transparent text-[#F4EBDD] border border-[rgba(191,145,51,0.3)] hover:border-[#F0AE2C] hover:bg-[#F0AE2C]/5",
      ghost:
        "bg-transparent text-[#A69A87] hover:text-[#F4EBDD] hover:bg-white/5",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
        {...props}
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
            <svg
              className="animate-spin h-4 w-4 text-current"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span>Loading...</span>
          </span>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";
