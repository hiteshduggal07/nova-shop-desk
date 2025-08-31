import React from 'react';

interface SaturnIconProps {
  className?: string;
  size?: number;
}

export const SaturnIcon: React.FC<SaturnIconProps> = ({ 
  className = "w-5 h-5", 
  size = 20 
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Saturn ring */}
      <ellipse
        cx="12"
        cy="12"
        rx="8"
        ry="3"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        opacity="0.8"
      />
      {/* Saturn planet */}
      <circle
        cx="12"
        cy="12"
        r="4"
        fill="currentColor"
      />
      {/* Inner glow effect */}
      <circle
        cx="12"
        cy="12"
        r="3"
        fill="url(#saturnGradient)"
        opacity="0.3"
      />
      {/* Gradient definition */}
      <defs>
        <radialGradient id="saturnGradient" cx="0.3" cy="0.3" r="0.7">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.8" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </radialGradient>
      </defs>
    </svg>
  );
};
