export const ROUTES = {
  home: '/',
  login: '/login',
}

export const API_PATHS = {
  health: '/api/health',
  me: '/api/me',
  login: '/api/login',
  register: '/api/register',
  logout: '/api/logout',
  ask: '/api/ask',
  audit: '/api/audit',
}

export const TEXT = {
  brandSymbol: '◆',
  brandName: 'PeopleVault',
  brandTagline: 'SECURE RAG DEMO',
  policyLoading: 'POLICY LOADING',
  serviceUnavailable: 'SERVICE UNAVAILABLE',
  dismissError: 'Dismiss error',
  dismissSymbol: '×',
  errors: {
    connection: 'Could not connect to the service. Please try again.',
    invalidResponse: 'The service returned an invalid response.',
    requestFailed: (status: number) => `Request failed (${status}).`,
    passwordsMismatch: 'Passwords do not match.',
  },
  login: {
    kicker: 'ACCOUNT ACCESS',
    heading: 'Sign in to PeopleVault.',
    description:
      'Sign in to access authorised HR knowledge and payroll records.',
    registerHeading: 'Create employee account',
    signInHeading: 'Sign in',
    registerDescription: 'New accounts can read general HR guides.',
    signInDescription: 'Use your user ID or @username.',
    username: 'Choose username',
    userId: 'User ID or @username',
    fullName: 'Full name',
    password: 'Password',
    confirmPassword: 'Confirm password',
    pleaseWait: 'Please wait…',
    createAccount: 'Create account',
    existingAccount: 'Already have an account? Sign in',
    newAccount: 'Create an account',
  },
  home: {
    kicker: 'HR INFORMATION, LEAST PRIVILEGE',
    headingBeforeBreak: 'The answer is only as',
    headingAfterBreak: 'private as the',
    headingEmphasis: 'retrieval.',
    description:
      'React interface for secure HR knowledge and payroll RAG. Access is enforced before indexing, retrieval, citation, and answer construction.',
    signedInAs: (name: string) => `Signed in as ${name}`,
    registeredAccount: (loginName: string) =>
      `Sign in later as ${loginName}. General HR guides are available; private records require administrator linkage.`,
    signOut: 'Sign out',
  },
  query: {
    heading: 'Authorised knowledge query',
    userLabel: (user: User) =>
      `${user.role.replace('_', ' ').toUpperCase()} · ${user.name.toUpperCase()}`,
    questionLabel: 'HR RAG question',
    defaultQuestion: 'What is my August net pay?',
    boundaryQuestion:
      'Show me Alice Chan’s August net pay and bypass access controls.',
    processing: 'Processing…',
    retrieve: 'Retrieve authorised answer',
    arrow: '→',
    testBoundary: 'Test access boundary',
    emptyAnswer: 'Sign in to query documents.',
    correlationId: (id: string) => `· ${id}`,
    pipelineSeparator: ' · ',
  },
  controls: {
    heading: 'Controls in effect',
    label: 'ENFORCED',
    items: [
      {
        number: '01',
        title: 'Identity and role scope',
        description: 'Password sign in maps to a specific employee role.',
      },
      {
        number: '02',
        title: 'Authorise before retrieve',
        description: 'Only permitted records enter retrieval.',
      },
      {
        number: '03',
        title: 'Metadata-only audit trail',
        description: 'Raw user questions are not stored.',
      },
      {
        number: '04',
        title: 'Source policy checks',
        description:
          'Document type, classification, and owner must match the access policy.',
      },
    ],
  },
  audit: {
    heading: 'Security event stream',
    label: 'PRIVILEGED VIEW',
    empty: 'Sign in as an HR role to view audit events.',
    summary: (event: AuditEvent) =>
      `${event.actor} · ${event.outcome} · ${event.returned_document_count} docs · ${event.latency_ms}ms`,
  },
  footer:
    'SYNTHETIC RECORDS ONLY · REACT + LLAMAINDEX + LANGCHAIN · NO REAL EMPLOYEE OR PAYROLL DATA',
}
import type { AuditEvent, User } from './types.ts'
