import React from 'react';
import { Typography, Container } from '@material-ui/core';

export default function Home() {
  return (
    <Container maxWidth="sm">
      <Typography variant="h1" component="h1" gutterBottom>
        Release Plan Dashboard
      </Typography>
      <Typography variant="body1">
        Welcome to the new Next.js-based Release Plan Dashboard.
      </Typography>
    </Container>
  );
}
