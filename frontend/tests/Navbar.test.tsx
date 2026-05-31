import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Navbar } from '../src/components/Navbar'

describe('Navbar', () => {
  it('renders navigation tabs', () => {
    const mockSetActiveTab = vi.fn()
    const mockOnSearchOpen = vi.fn()

    render(
      <Navbar
        activeTab="leagues"
        setActiveTab={mockSetActiveTab}
        onSearchOpen={mockOnSearchOpen}
      />
    )

    expect(screen.getByText('Leagues')).toBeInTheDocument()
    expect(screen.getByText('Rise & Fall')).toBeInTheDocument()
    expect(screen.getByText('Team Form')).toBeInTheDocument()
  })

  it('calls setActiveTab when tab is clicked', async () => {
    const user = userEvent.setup()
    const mockSetActiveTab = vi.fn()
    const mockOnSearchOpen = vi.fn()

    render(
      <Navbar
        activeTab="leagues"
        setActiveTab={mockSetActiveTab}
        onSearchOpen={mockOnSearchOpen}
      />
    )

    const riseTab = screen.getByRole('button', { name: /Rise & Fall/ })
    await user.click(riseTab)

    expect(mockSetActiveTab).toHaveBeenCalledWith('risefall')
  })
})
