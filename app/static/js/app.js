document.addEventListener("DOMContentLoaded", () => {
  const items = document.getElementById("items");
  const add = document.getElementById("add-row");
  if (!items || !add) return;
  const calculate = () => {
    let subtotal = 0;
    items.querySelectorAll(".item-row").forEach(row => {
      const select = row.querySelector(".product-select");
      const qty = Number(row.querySelector(".qty").value || 0);
      const price = Number(select.selectedOptions[0]?.dataset.price || 0);
      const amount = price * qty;
      row.querySelector(".line-total").textContent = "₹" + amount.toFixed(2);
      subtotal += amount;
    });
    const discount = Math.min(20, Math.max(0, Number(document.getElementById("discount").value || 0)));
    const discountAmount = subtotal * discount / 100;
    document.getElementById("subtotal").textContent = "₹" + subtotal.toFixed(2);
    document.getElementById("discount-amount").textContent = "₹" + discountAmount.toFixed(2);
    document.getElementById("grand-total").textContent = "₹" + (subtotal-discountAmount).toFixed(2);
  };
  const bind = row => {
    row.querySelectorAll("select,input").forEach(el => el.addEventListener("change", calculate));
    row.querySelector(".remove-row").addEventListener("click", () => {
      if (items.querySelectorAll(".item-row").length > 1) row.remove();
      calculate();
    });
  };
  bind(items.querySelector(".item-row"));
  add.addEventListener("click", () => {
    const row = items.querySelector(".item-row").cloneNode(true);
    row.querySelector("select").selectedIndex = 0;
    row.querySelector(".qty").value = 1;
    items.appendChild(row); bind(row); calculate();
  });
  document.getElementById("discount").addEventListener("input", calculate);
  document.getElementById("order-form").addEventListener("submit", event => {
    const button = event.currentTarget.querySelector('button[type="submit"]');
    if (!event.currentTarget.reportValidity()) { event.preventDefault(); return; }
    button.disabled = true; button.textContent = "Saving...";
  });
  calculate();
});
