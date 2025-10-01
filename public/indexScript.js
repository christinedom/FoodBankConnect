// const isMobile =
//   typeof window.orientation !== "undefined" ||
//   navigator.userAgent.indexOf("IEMobile") !== -1;

// if (isMobile) {
//   window.location = "/mobile.php";
// }

// function lazyLoadImages() {
// 	const lazyImages = document.querySelectorAll(".lazyimage");

// 	let i = 0;
// 	const loadNextImage = () => {
// 		if (i < lazyImages.length) {
// 			const image = lazyImages[i];
// 			const src = image.getAttribute("data-lazy");
// 			image.setAttribute("src", src);
// 			image.classList.remove("lazyimage");
// 			i++;
// 			image.onload = () => {
// 				loadNextImage();
// 				image.classList.add("fade-in");
// 			};
// 		}
// 	};

// 	loadNextImage();
// }

// window.addEventListener("load", lazyLoadImages);

function adjustScroll() {
  const scrollbar = document.getElementById("scrollbar");
  const thumb = document.getElementById("scrollthumb");
  const scrollEl = document.scrollingElement || document.documentElement;

  // Use fractional pixel sizes to avoid zoom/DPR rounding issues
  const barWidth = scrollbar.getBoundingClientRect().width;
  const thumbWidth = thumb.getBoundingClientRect().width;

  const maxScroll = Math.max(0, scrollEl.scrollWidth - scrollEl.clientWidth);
  const progress = maxScroll > 0 ? scrollEl.scrollLeft / maxScroll : 0;

  const maxThumbX = Math.max(0, barWidth - thumbWidth);
  const thumbX = Math.min(maxThumbX, Math.max(0, progress * maxThumbX));

  // Position relative to the scrollbar wrapper
  thumb.style.left = `${thumbX}px`;
}

window.addEventListener("DOMContentLoaded", adjustScroll);
window.addEventListener("resize", adjustScroll);
window.addEventListener("scroll", adjustScroll, { passive: true });
