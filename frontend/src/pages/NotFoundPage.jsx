import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-[#FAFAFA] flex flex-col items-center justify-center p-4">
      <div className="bg-white rounded-[24px] shadow-lg border border-gray-100 p-8 sm:p-12 w-full max-w-md text-center">
        <h1 className="text-4xl font-bold text-teal-800 mb-4">404</h1>
        <p className="text-gray-600 mb-8">Oops! The page you're looking for doesn't exist.</p>
        <Link 
          to="/"
          className="inline-block bg-teal-700 hover:bg-teal-600 text-white font-semibold px-6 py-3 rounded-xl transition-all shadow-md hover:shadow-lg active:scale-[0.98]"
        >
          Return to App
        </Link>
      </div>
    </div>
  );
}
