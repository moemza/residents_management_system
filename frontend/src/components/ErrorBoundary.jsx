import { Component } from "react";

/**
 * Last-resort render boundary.
 *
 * A rendering exception in any page would otherwise leave a blank document.
 * The fallback offers a reload rather than trying to re-render the failing
 * tree, which is unlikely to recover without new data.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    // Keep the log deliberately terse: component stacks can include props.
    console.error("Unhandled UI error:", error?.name || "Error");
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="container mt-5" role="alert">
        <h1 className="h3">Something went wrong</h1>
        <p>
          The page could not be displayed. Reload the application to try again.
          No data has been changed by this error.
        </p>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => window.location.assign("/")}
        >
          Reload application
        </button>
      </div>
    );
  }
}
