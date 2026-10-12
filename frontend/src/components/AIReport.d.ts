import * as React from 'react';
export default function AIReport(props: {
  response?: unknown;
  loading?: boolean;
  error?: string;
  title?: string;
  model?: string;
  tokens?: number | Record<string, number>;
}): React.ReactElement | null;
