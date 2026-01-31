import React from "react";
import { useEffect } from "react";
import { createContext, useState, useContext } from "react";

const CartContext = createContext();

export const CartProvider = ({ children }) => {
    const [cart, setCart] = useState([]);

    const fetchCart = async () => {
        try {
            const response = await fetch("http://127.0.0.1:8000/api/cart/");
            const data = await response.json();
            setCart(data);
        } catch (err) {
            console.error("Fetch Error:", err);
        }
    };

    useEffect(() => {
        fetchCart();
    }, []);

    const updateQuantity = async (productId, newQuantity) => {
        if (newQuantity < 1) return;

        setCart((prev) =>
            prev.map((item) =>
                item.product_id === productId
                    ? { ...item, quantity: newQuantity }
                    : item
            )
        );

        try {
            await fetch(`http://127.0.0.1:8000/api/cart/${productId}/`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ quantity: newQuantity }),
            });
        } catch (err) {
            console.error("Failed to update quantity:", err);
        }
    };

    const removeFromCart = async (productId) => {
        setCart((prev) => prev.filter((item) => item.product_id !== productId));

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/api/cart/${productId}/`,
                {
                    // Ensure slash at the end
                    method: "DELETE",
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            );

            if (!response.ok) {
                console.error("Server responded with error:", response.status);
                // If it failed, refresh the cart from server to show reality
                fetchCart();
            }
        } catch (err) {
            console.error("Network error:", err);
            fetchCart();
        }
    };

    const addToCart = async (product) => {
        try {
            const response = await fetch("http://127.0.0.1:8000/api/cart/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ product_id: product.product_id }),
            });
            if (response.ok) fetchCart();
        } catch (err) {
            console.error("Network Error:", err);
        }
    };

    return (
        <CartContext.Provider
            value={{ cart, addToCart, removeFromCart, updateQuantity }}
        >
            {children}
        </CartContext.Provider>
    );
};
export const useCart = () => useContext(CartContext);
