import React from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "gold" | "neutral" | "subtle";
  size?: "sm" | "md";
}

export function Badge({
  children,
  variant = "gold",
  size = "md",
  className = "",
  ...props
}: BadgeProps) {
  const sizeStyles = {
    sm: "px-2 py-0.5 text-[10px] tracking-widest",
    md: "px-3 py-1 text-xs tracking-wider",
  };

  const variantStyles = {
    gold: "text-[#F0AE2C] bg-[#F0AE2C]/10 border border-[#F0AE2C]/30",
    neutral: "text-[#F4EBDD] bg-[#11100E] border border-[rgba(191,145,51,0.2)]",
    subtle: "text-[#A69A87] bg-white/[0.03] border border-white/10",
  };

  return (
    <span
      className={`inline-flex items-center uppercase font-semibold rounded-full select-none ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
