import React from 'react';
import { Verdict, InspectionStatus } from '../types/inspection';

interface StatusBadgeProps {
  verdict?: Verdict | string | null;
  status?: InspectionStatus | string | null;
  size?: 'sm' | 'md' | 'lg';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ verdict, status, size = 'md' }) => {
  const value = verdict || status || 'PENDING';
  const valUpper = value.toUpperCase();

  let badgeClass = 'badge-completed';
  let icon = '•';
  let label = valUpper;

  if (valUpper === 'PASS') {
    badgeClass = 'badge-pass';
    icon = '✓';
    label = 'PASS';
  } else if (valUpper === 'FAIL') {
    badgeClass = 'badge-fail';
    icon = '✕';
    label = 'FAIL';
  } else if (valUpper === 'UNCERTAIN') {
    badgeClass = 'badge-uncertain';
    icon = '?';
    label = 'UNCERTAIN';
  } else if (valUpper === 'PENDING_REVIEW' || valUpper === 'PENDING REVIEW') {
    badgeClass = 'badge-pending_review';
    icon = '⏳';
    label = 'PENDING REVIEW';
  } else if (valUpper === 'PENDING') {
    badgeClass = 'badge-pending';
    icon = '○';
    label = 'PENDING';
  } else if (valUpper === 'COMPLETED') {
    badgeClass = 'badge-completed';
    icon = '✓';
    label = 'COMPLETED';
  }

  const sizeClass = size === 'lg' ? 'badge-lg' : size === 'sm' ? 'btn-sm' : '';

  return (
    <span className={`badge ${badgeClass} ${sizeClass}`} data-testid={`badge-${label.toLowerCase().replace(' ', '_')}`}>
      <span>{icon}</span>
      <span>{label}</span>
    </span>
  );
};
