import { Layout } from './components/Layout';

function App() {
  return (
    <Layout>
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8">
        <h2 className="text-2xl font-semibold text-slate-900">Welcome to QueryMate AI</h2>
        <p className="mt-2 text-slate-600">
          Frontend setup complete. Query interface coming in the next PR.
        </p>
      </div>
    </Layout>
  );
}

export default App;
