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
            console.error("Errorfetching cart:", err);
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
            await requester.patch(`/api/cart/${productId}/`, {
                quantity: newQuantity,
            });
        } catch (err) {
            console.error("Error updating quantity:", err);
            await fetchCart(); // Revert on error
        }
    };

    const removeFromCart = async (productId) => {
        setCart((prev) => prev.filter((item) => item.id !== productId));

        try {
            await requester.delete(`/api/cart/${productId}/`);
        } catch (err) {
            console.error("Error removing from cart:", err);
            await fetchCart(); // Revert on error
        }
    };

    const addToCart = async (product) => {
        console.log("Adding product to cart:", product);
        try {
            const response = await requester.post("/api/cart/", {
                id: product.id,
            });

            console.log("Response status:", response.status);
            console.log("Response data:", response.data);

            if (response.status === 200 || response.status === 201) {
                await fetchCart();
                return true;
            }
            return false;
        } catch (err) {
            console.error("Error adding to cart:", err);
            if (err.response) {
                console.error(
                    "Server responded with:",
                    err.response.status,
                    err.response.data
                );
            }
            return false;
        }
    };

    const clearCart = async () => {
        const ids = cart.map((item) => item.id);
        try {
            await Promise.all(
                ids.map((id) => requester.delete(`/api/cart/${id}/`))
            );
            setCart([]);
        } catch (err) {
            console.error("Error clearing cart:", err);
            await fetchCart();
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
