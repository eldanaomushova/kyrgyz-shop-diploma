import React, { useEffect, useState, useContext, createContext } from "react";
import { requester } from "../../utils/Requester/Requester";

const CartContext = createContext();

export const CartProvider = ({ children }) => {
    const [cart, setCart] = useState([]);
    const fetchCart = async () => {
        try {
            const response = await requester.get("/api/cart/");
            setCart(response.data);
            return response.data;
        } catch (err) {
            setCart([]);
            return [];
        }
    };

    useEffect(() => {
        fetchCart();
    }, []);

    const updateQuantity = async (productId, newQuantity) => {
        if (newQuantity < 1) return;

        setCart((prev) =>
            prev.map((item) =>
                item.id === productId
                    ? { ...item, quantity: newQuantity }
                    : item
            )
        );

        try {
            const response = await fetch(`/api/cart/${productId}/`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ quantity: newQuantity }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (err) {
            fetchCart();
        }
    };

    const removeFromCart = async (productId) => {
        setCart((prev) => prev.filter((item) => item.id !== productId));

        try {
            const response = await fetch(`/api/cart/${productId}/`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
            });

            if (!response.ok) {
                fetchCart();
            }
        } catch (err) {
            fetchCart();
        }
    };

    const addToCart = async (product) => {
        console.log("Adding product to cart:", product);
        try {
            const response = await fetch("/api/cart/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id: product.id }),
            });

            console.log("Response status:", response.status);
            const responseData = await response.json();
            console.log("Response data:", responseData);

            if (response.ok) {
                await fetchCart();
                return true;
            }
            return false;
        } catch (err) {
            console.error("Error:", err);
            return false;
        }
    };

    const clearCart = async () => {
        const ids = cart.map((item) => item.id);
        try {
            await Promise.all(
                ids.map((id) =>
                    fetch(`/api/cart/${id}/`, {
                        method: "DELETE",
                        headers: { "Content-Type": "application/json" },
                    })
                )
            );
            setCart([]);
        } catch (err) {
            fetchCart();
        }
    };

    const getCartTotal = () => {
        return cart.reduce((total, item) => {
            const price = item.price || item.product?.price || 0;
            return total + price * item.quantity;
        }, 0);
    };

    const getCartItemCount = () => {
        return cart.reduce((count, item) => count + item.quantity, 0);
    };

    return (
        <CartContext.Provider
            value={{
                cart,
                addToCart,
                removeFromCart,
                updateQuantity,
                clearCart,
                getCartTotal,
                getCartItemCount,
                fetchCart,
            }}
        >
            {children}
        </CartContext.Provider>
    );
};

export const useCart = () => {
    const context = useContext(CartContext);
    if (!context) {
        throw new Error("useCart must be used within a CartProvider");
    }
    return context;
};
