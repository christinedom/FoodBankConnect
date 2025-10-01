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
  let thumb = document.getElementById("scrollthumb");
  let bar = document.getElementById("scrollbody");
  const bar_width = Math.max(
    bar.scrollWidth,
    bar.offsetWidth,
    bar.clientWidth,
    bar.scrollWidth,
    bar.offsetWidth,
  );
  const limit =
    Math.max(
      document.body.scrollWidth,
      document.body.offsetWidth,
      document.documentElement.clientWidth,
      document.documentElement.scrollWidth,
      document.documentElement.offsetWidth,
    ) - window.innerWidth;
  thumb.style.transform = `translateX(${
    bar_width *
    ((window.scrollX - thumb.getBoundingClientRect().width) /
      (limit + thumb.getBoundingClientRect().width))
  }px)`;
}

window.addEventListener("scroll", adjustScroll);
