// Cart and Wishlist Management
document.addEventListener('DOMContentLoaded', function() {
    updateBadges();
});

// Update cart and wishlist badge counts
function updateBadges() {
    const cartCount = getCartCount();
    const wishlistCount = getWishlistCount();
    
    document.querySelectorAll('#cart-count').forEach(el => {
        el.textContent = cartCount;
        el.style.display = cartCount > 0 ? 'inline-block' : 'none';
    });
    
    document.querySelectorAll('#wishlist-count').forEach(el => {
        el.textContent = wishlistCount;
        el.style.display = wishlistCount > 0 ? 'inline-block' : 'none';
    });
}

// Get cart count from session
function getCartCount() {
    // This will be updated by server responses
    const badge = document.querySelector('#cart-count');
    return badge ? parseInt(badge.textContent) || 0 : 0;
}

// Get wishlist count from session
function getWishlistCount() {
    const badge = document.querySelector('#wishlist-count');
    return badge ? parseInt(badge.textContent) || 0 : 0;
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// View product detail
function viewProduct(productId) {
    window.location.href = `/product/${productId}`;
}

// Add to cart
function addToCart(productId) {
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: productId, quantity: 1 })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Added to cart!', 'success');
            document.querySelectorAll('#cart-count').forEach(el => {
                el.textContent = data.cart_count;
                el.style.display = 'inline-block';
            });
        }
    })
    .catch(error => {
        showToast('Error adding to cart', 'error');
        console.error('Error:', error);
    });
}

// Add to cart with quantity (from product detail page)
function addToCartWithQuantity(productId) {
    const quantity = parseInt(document.getElementById('quantity').value) || 1;
    
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: productId, quantity: quantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Added ${quantity} item(s) to cart!`, 'success');
            document.querySelectorAll('#cart-count').forEach(el => {
                el.textContent = data.cart_count;
                el.style.display = 'inline-block';
            });
        }
    })
    .catch(error => {
        showToast('Error adding to cart', 'error');
        console.error('Error:', error);
    });
}

// Buy now (add to cart and redirect to checkout)
function buyNow(productId) {
    const quantity = parseInt(document.getElementById('quantity')?.value) || 1;
    
    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: productId, quantity: quantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/checkout';
        }
    })
    .catch(error => {
        showToast('Error processing request', 'error');
        console.error('Error:', error);
    });
}

// Update cart quantity
function updateCartQuantity(productId, newQuantity) {
    if (newQuantity < 1) {
        removeFromCart(productId);
        return;
    }
    
    fetch('/api/cart/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: productId, quantity: newQuantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Reload to update totals
        }
    })
    .catch(error => {
        showToast('Error updating cart', 'error');
        console.error('Error:', error);
    });
}

// Remove from cart
function removeFromCart(productId) {
    if (!confirm('Remove this item from cart?')) return;
    
    fetch('/api/cart/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: productId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Removed from cart', 'success');
            location.reload();
        }
    })
    .catch(error => {
        showToast('Error removing item', 'error');
        console.error('Error:', error);
    });
}

// Toggle wishlist
function toggleWishlist(productId, event) {
    if (event) event.preventDefault();
    
    const btn = event?.currentTarget;
    const isInWishlist = btn?.classList.contains('active');
    
    const endpoint = isInWishlist ? '/api/wishlist/remove' : '/api/wishlist/add';
    
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ product_id: productId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (isInWishlist) {
                showToast('Removed from wishlist', 'success');
                btn?.classList.remove('active');
                btn?.querySelector('i')?.classList.replace('fas', 'far');
                // If on wishlist page, remove the card
                if (window.location.pathname === '/wishlist') {
                    location.reload();
                }
            } else {
                showToast('Added to wishlist!', 'success');
                btn?.classList.add('active');
                btn?.querySelector('i')?.classList.replace('far', 'fas');
            }
            
            document.querySelectorAll('#wishlist-count').forEach(el => {
                el.textContent = data.wishlist_count;
                el.style.display = data.wishlist_count > 0 ? 'inline-block' : 'none';
            });
        }
    })
    .catch(error => {
        showToast('Error updating wishlist', 'error');
        console.error('Error:', error);
    });
}

// Remove from wishlist
function removeFromWishlist(productId, event) {
    toggleWishlist(productId, event);
}

// Change quantity on product detail page
function changeQuantity(delta) {
    const input = document.getElementById('quantity');
    if (!input) return;
    
    const currentValue = parseInt(input.value) || 1;
    const maxValue = parseInt(input.max) || 999;
    const newValue = Math.max(1, Math.min(maxValue, currentValue + delta));
    
    input.value = newValue;
}

// Complete checkout
function completeCheckout() {
    const form = document.getElementById('checkout-form');
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Show loading state
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    fetch('/api/checkout/complete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            // In a real app, you'd collect and send form data here
            firstName: document.getElementById('firstName').value,
            lastName: document.getElementById('lastName').value,
            email: document.getElementById('email').value,
            // ... etc
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = '/order-success';
        } else {
            showToast('Error processing order', 'error');
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    })
    .catch(error => {
        showToast('Error processing order', 'error');
        console.error('Error:', error);
        btn.disabled = false;
        btn.innerHTML = originalText;
    });
}
