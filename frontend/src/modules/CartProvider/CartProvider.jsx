import React, { useEffect, useState, useContext, createContext } from "react";

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
                item.id === productId
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
        setCart((prev) => prev.filter((item) => item.id !== productId));

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
                body: JSON.stringify({ id: product.id }),
            });
            if (response.ok) fetchCart();
        } catch (err) {
            console.error("Network Error:", err);
        }
    };

    const clearCart = async () => {
        const ids = cart.map((item) => item.id);
        try {
            await Promise.all(
                ids.map((id) =>
                    fetch(`http://127.0.0.1:8000/api/cart/${id}/`, {
                        method: "DELETE",
                        headers: { "Content-Type": "application/json" },
                    })
                )
            );
        } catch (err) {
            console.error("Failed to clear cart items:", err);
        } finally {
            setCart([]);
        }
    };

    return (
        <CartContext.Provider
            value={{
                cart,
                addToCart,
                removeFromCart,
                updateQuantity,
                clearCart,
            }}
        >
            {children}
        </CartContext.Provider>
    );
};
export const useCart = () => useContext(CartContext);
