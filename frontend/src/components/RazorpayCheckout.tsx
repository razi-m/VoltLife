/**
 * RazorpayCheckout.tsx — additive Razorpay Checkout button (Stripe components untouched).
 *
 * Flow:
 *   1. POST /api/v1/payments/razorpay/create-order { quote_id } -> { razorpay_order_id, key_id, amount, currency }
 *   2. Open the Razorpay Checkout modal (loaded from the official checkout.js script — no npm dep).
 *   3. On success, POST /api/v1/payments/razorpay/verify (signature) -> backend reuses the existing
 *      order-creation + inventory-lock + logistics flow.
 *
 * Demo: with NO Razorpay keys the backend returns a MOCK order id; this component still opens a
 * (test) modal if a key is present, or you can wire a "Simulate payment" fallback that posts a mock
 * verify payload. No real money is moved.
 */
import { useState } from 'react';

const API_BASE = (import.meta as any).env?.VITE_API_URL || ((import.meta as any).env?.PROD ? '' : 'http://localhost:8000');

declare global {
  interface Window { Razorpay?: any }
}

function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const s = document.createElement('script');
    s.src = 'https://checkout.razorpay.com/v1/checkout.js';
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
}

interface Props {
  quoteId: number;
  authToken: string;                 // buyer bearer token
  buyerName?: string;
  buyerEmail?: string;
  onSuccess?: (order: any) => void;
  onError?: (message: string) => void;
}

export default function RazorpayCheckout({ quoteId, authToken, buyerName, buyerEmail, onSuccess, onError }: Props) {
  const [loading, setLoading] = useState(false);

  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${authToken}`,
  };

  async function handlePay() {
    setLoading(true);
    try {
      // 1. Create Razorpay order on the backend
      const orderRes = await fetch(`${API_BASE}/api/v1/payments/razorpay/create-order`, {
        method: 'POST', headers, body: JSON.stringify({ quote_id: quoteId }),
      });
      if (!orderRes.ok) throw new Error('Failed to create Razorpay order');
      const order = await orderRes.json(); // { razorpay_order_id, key_id, amount, currency, demo_mode }

      const verify = async (payment: { razorpay_payment_id: string; razorpay_signature: string }) => {
        const vr = await fetch(`${API_BASE}/api/v1/payments/razorpay/verify`, {
          method: 'POST', headers,
          body: JSON.stringify({
            quote_id: quoteId,
            razorpay_order_id: order.razorpay_order_id,
            razorpay_payment_id: payment.razorpay_payment_id,
            razorpay_signature: payment.razorpay_signature,
          }),
        });
        if (!vr.ok) { onError?.('Payment verification failed'); return; }
        onSuccess?.(await vr.json());
      };

      // 2. Open the Razorpay modal (real test mode) OR mock-confirm (keyless demo)
      const ok = await loadRazorpayScript();
      if (ok && window.Razorpay && !order.demo_mode) {
        const rzp = new window.Razorpay({
          key: order.key_id,
          amount: order.amount,
          currency: order.currency,
          name: 'VoltLife',
          description: 'Second-life battery purchase (TEST)',
          order_id: order.razorpay_order_id,
          prefill: { name: buyerName || '', email: buyerEmail || '' },
          handler: (resp: any) => verify({
            razorpay_payment_id: resp.razorpay_payment_id,
            razorpay_signature: resp.razorpay_signature,
          }),
          theme: { color: '#1FB6A8' },
        });
        rzp.open();
      } else {
        // Keyless DEMO: backend accepts MOCK order ids; submit a mock verify payload.
        await verify({ razorpay_payment_id: 'pay_MOCKDEMO', razorpay_signature: 'mock_signature' });
      }
    } catch (e: any) {
      onError?.(e?.message || 'Payment error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <button className="btn-primary" onClick={handlePay} disabled={loading}>
      {loading ? 'Processing…' : 'Pay with Razorpay'}
    </button>
  );
}
