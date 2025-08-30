import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CheckCircle, Package, Truck, Mail, ArrowRight, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';

interface OrderData {
  id: string;
  items: Array<{
    product: {
      id: string;
      name: string;
      price: number;
      image: string;
    };
    quantity: number;
  }>;
  subtotal: number;
  shipping: number;
  tax: number;
  total: number;
  customerInfo: {
    name: string;
    email: string;
    address: string;
  };
  orderDate: string;
}

export default function OrderSuccess() {
  const [orderData, setOrderData] = useState<OrderData | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const savedOrder = localStorage.getItem('lastOrder');
    if (savedOrder) {
      setOrderData(JSON.parse(savedOrder));
    } else {
      // If no order found, redirect to home
      navigate('/');
    }
  }, [navigate]);

  if (!orderData) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <p className="text-muted-foreground">Loading order details...</p>
        </div>
      </div>
    );
  }

  const estimatedDelivery = new Date();
  estimatedDelivery.setDate(estimatedDelivery.getDate() + 5); // 5 days from now

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Success Header */}
      <div className="text-center mb-8">
        <div className="w-20 h-20 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-12 h-12 text-accent" />
        </div>
        <h1 className="text-3xl md:text-4xl font-heading font-bold mb-4">
          Order Confirmed!
        </h1>
        <p className="text-muted-foreground text-lg mb-2">
          Thank you for your purchase, {orderData.customerInfo.name.split(' ')[0]}!
        </p>
        <p className="text-muted-foreground">
          Your order <span className="font-medium text-foreground">{orderData.id}</span> has been successfully placed.
        </p>
      </div>

      {/* Order Timeline */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="text-center">
          <div className="w-12 h-12 bg-accent rounded-full flex items-center justify-center mx-auto mb-3">
            <CheckCircle className="w-6 h-6 text-white" />
          </div>
          <h3 className="font-semibold text-sm">Order Placed</h3>
          <p className="text-muted-foreground text-xs">
            {new Date(orderData.orderDate).toLocaleDateString()}
          </p>
        </div>
        <div className="text-center">
          <div className="w-12 h-12 bg-muted border-2 border-accent rounded-full flex items-center justify-center mx-auto mb-3">
            <Package className="w-6 h-6 text-accent" />
          </div>
          <h3 className="font-semibold text-sm">Processing</h3>
          <p className="text-muted-foreground text-xs">1-2 business days</p>
        </div>
        <div className="text-center">
          <div className="w-12 h-12 bg-muted border-2 border-muted-foreground rounded-full flex items-center justify-center mx-auto mb-3">
            <Truck className="w-6 h-6 text-muted-foreground" />
          </div>
          <h3 className="font-semibold text-sm text-muted-foreground">Delivered</h3>
          <p className="text-muted-foreground text-xs">
            Est. {estimatedDelivery.toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Order Details */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Order Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {orderData.items.map((item) => (
                <div key={item.product.id} className="flex gap-4">
                  <div className="w-16 h-16 flex-shrink-0">
                    <img
                      src={item.product.image}
                      alt={item.product.name}
                      className="w-full h-full object-cover rounded-lg"
                    />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium line-clamp-2">{item.product.name}</h3>
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-muted-foreground text-sm">
                        Qty: {item.quantity}
                      </span>
                      <span className="font-medium">
                        ${(item.product.price * item.quantity).toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}

              <Separator />

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>${orderData.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Shipping</span>
                  <span>
                    {orderData.shipping === 0 ? 'Free' : `$${orderData.shipping.toFixed(2)}`}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Tax</span>
                  <span>${orderData.tax.toFixed(2)}</span>
                </div>
                <Separator />
                <div className="flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>${orderData.total.toFixed(2)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Shipping & Actions */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Shipping Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium mb-1">Delivery Address</h4>
                <p className="text-muted-foreground text-sm">
                  {orderData.customerInfo.name}<br />
                  {orderData.customerInfo.address}
                </p>
              </div>
              
              <div>
                <h4 className="font-medium mb-1">Estimated Delivery</h4>
                <p className="text-muted-foreground text-sm">
                  {estimatedDelivery.toLocaleDateString()} (5-7 business days)
                </p>
              </div>

              <div>
                <h4 className="font-medium mb-1">Tracking</h4>
                <p className="text-muted-foreground text-sm">
                  You'll receive a tracking number via email once your order ships.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>What's Next?</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 text-primary mt-0.5" />
                <div>
                  <h4 className="font-medium text-sm">Order Confirmation</h4>
                  <p className="text-muted-foreground text-xs">
                    Check your email at {orderData.customerInfo.email} for order details
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <Package className="w-5 h-5 text-primary mt-0.5" />
                <div>
                  <h4 className="font-medium text-sm">Order Processing</h4>
                  <p className="text-muted-foreground text-xs">
                    We'll prepare your items and send you shipping updates
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <Truck className="w-5 h-5 text-primary mt-0.5" />
                <div>
                  <h4 className="font-medium text-sm">Tracking Updates</h4>
                  <p className="text-muted-foreground text-xs">
                    Follow your package with real-time tracking updates
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button className="w-full">
              <Download className="w-4 h-4 mr-2" />
              Download Receipt
            </Button>
            
            <Link to="/products" className="block">
              <Button variant="outline" className="w-full">
                Continue Shopping
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-12 text-center p-6 bg-muted/50 rounded-lg">
        <h3 className="font-semibold mb-2">Need Help?</h3>
        <p className="text-muted-foreground text-sm mb-4">
          Have questions about your order? We're here to help!
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button variant="outline" size="sm">
            Contact Support
          </Button>
          <Button variant="outline" size="sm">
            Track Your Order
          </Button>
        </div>
      </div>
    </div>
  );
}