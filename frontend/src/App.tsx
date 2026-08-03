import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AccountsPage } from './pages/AccountsPage'
import { BillsPage } from './pages/BillsPage'
import { CoachPage } from './pages/CoachPage'
import { DashboardPage } from './pages/DashboardPage'
import { DebtPage } from './pages/DebtPage'
import { ExpensesPage } from './pages/ExpensesPage'
import { ForecastingPage } from './pages/ForecastingPage'
import { GoalsPage } from './pages/GoalsPage'
import { HistoryPage } from './pages/HistoryPage'
import { IncomePage } from './pages/IncomePage'
import { RecommendationsPage } from './pages/RecommendationsPage'
import { RecurringExpensesPage } from './pages/RecurringExpensesPage'
import { ScenariosPage } from './pages/ScenariosPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/expenses" element={<ExpensesPage />} />
          <Route path="/recurring-expenses" element={<RecurringExpensesPage />} />
          <Route path="/accounts" element={<AccountsPage />} />
          <Route path="/bills" element={<BillsPage />} />
          <Route path="/income" element={<IncomePage />} />
          <Route path="/debts" element={<DebtPage />} />
          <Route path="/goals" element={<GoalsPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/forecasting" element={<ForecastingPage />} />
          <Route path="/scenarios" element={<ScenariosPage />} />
          <Route path="/coach" element={<CoachPage />} />
          <Route path="/recommendations" element={<RecommendationsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
