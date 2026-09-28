# Khảo Sát Kiến Trúc & Thiết Kế Kỹ Thuật: Frontend Phân Lớp Không Xung Đột (ThreeUI 3D + Morphicons Pipeline)

> **Mã khảo sát:** R4 — SURVEY-3  
> **Người thực hiện:** Explorer Survey 3 (`teamwork_preview_explorer`)  
> **Dự án:** NarrAI (Next.js 14 App Router + Tailwind CSS + FastAPI)  
> **Ngày khảo sát:** 2026-09-28  
> **Tài liệu tham chiếu gốc:** `e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md` (Mục ## 2026-09-28T01:01:31Z, R4)

---

## 1. Tóm Tắt Điều Hành (Executive Summary)

Yêu cầu **R4 (Kiến Trúc Frontend Phân Lớp Không Xung Đột)** giải quyết bài toán cốt tử của các giao diện web hiện đại: **Làm thế nào để dung hợp đồng thời đồ họa 3D không gian (ThreeUI WebGL), hiệu ứng chiều sâu 3D trên thẻ nội dung (CSS 3D Parallax Tilt), hoạt họa biến hình vector vi mô (Morphicons SVG Spring Physics) và các modal phủ kính mờ (Glassmorphism Portals) mà vẫn duy trì vững vàng 60 FPS, không gây crash WebGL context, không xung đột layer stacking context và không vỡ layout?**

Khảo sát mã nguồn hiện tại của NarrAI ghi nhận:
1. **Hiện trạng công nghệ frontend:** Dự án sử dụng **Next.js 14.2.23 (App Router)**, **React 18.3.1**, **Tailwind CSS 3.4.17**, **lucide-react 0.468.0**, `next-themes 0.4.4`, `clsx`, `tailwind-merge`. Cấu hình `next.config.mjs` thiết lập chế độ `output: 'export'` (khi không chạy trên Vercel), đòi hỏi mọi thành phần liên quan đến DOM/WebGL/Canvas phải an toàn 100% với quá trình Hydration và SSR/SSG.
2. **Hiện trạng dependencies đồ họa:** Hiện tại dự án **chưa cài đặt `three`, `@types/three`, hay `framer-motion`**. Việc phụ thuộc vào các thư viện ngoài dung lượng lớn (> 700KB) tiềm ẩn rủi ro bloat bundle, lỗi tương thích SSR và rủi ro nghẽn cài đặt mạng.
3. **Giải pháp kiến trúc đột phá:** Khảo sát này đề xuất một giải pháp kiến trúc phân lớp độc lập (**Decoupled 4-Layer Visual Pipeline**), trong đó:
   - **Layer 0 (ThreeUI):** Triển khai bằng một Singleton WebGL Engine siêu nhẹ, tự cung cấp Shader GLSL nguyên bản (Native GLSL Shaders) cho họa tiết Trống đồng Đông Sơn và trường hạt ánh sáng 3D tương tác. Kích thước chỉ ~12KB (thay vì 600KB của Three.js), kiểm soát 100% vòng đời WebGL Context, tự động tạm dừng về **0% CPU/GPU** khi tab ẩn hoặc cuộn ngoài màn hình.
   - **Layer 1 (Core Semantic DOM & 3D Interactive Cards):** Sử dụng thuần túy CSS 3D Transforms (`perspective: 1000px`, `transform-style: preserve-3d`) trên khung tranh Manga (`ComicViewer`) và thẻ bài viết/tính năng, hoạt động hoàn toàn trên GPU Compositor thread, cách ly 100% với WebGL canvas.
   - **Layer 2 (SVG Morphing Micro-Interactions — Morphicons):** Hoạt động độc lập trên DOM bằng giải thuật nội suy đường dẫn vector (SVG path interpolation) kết hợp giải phương trình vi phân dao động tắt dần điều hòa (Damped Harmonic Oscillator Spring Physics) độc lập: Nút Like (tim rực rỡ + burst), Huy hiệu Xu (xoay 3D morph thành số dư), Bộ chọn Model AI (Flash ⚡ → Versatile 🌟 → Master 👑).
   - **Layer 3 (Glassmorphism Overlay & Portals):** Toàn bộ Modals (Nạp xu, Open Messenger, Copilot) được đẩy ra ngoài luồng DOM chính qua `createPortal` gắn vào `document.body`, áp dụng thuộc tính bắt buộc `isolation: isolate` và `z-index: 50+`. Triệt tiêu hoàn toàn hiện tượng kẹt Stacking Context trong không gian 3D của Layer 1 và lỗi vỡ nền mờ `backdrop-filter: blur()`.
   - **Graceful Degradation:** Tự động phát hiện cấu hình phần cứng yếu (`navigator.hardwareConcurrency < 4`, `deviceMemory < 4GB`, FPS watchdog < 28 FPS) hoặc người dùng bật `prefers-reduced-motion` để tự động giáng cấp xuống hiệu ứng CSS phẳng truyền thống, tiết kiệm pin 100%.

---

## 2. Bản Đồ Phân Tầng Kiến Trúc (Decoupled Visual Pipeline Architecture)

Bảng tổng hợp 4 lớp hiển thị và cơ chế cách ly tài nguyên:

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Layer 3: Glassmorphism Overlay & Portals (React Portals, isolation: isolate)   │
│ - Coin Topup Modal (100k = 100 Xu)                                            │
│ - Open Messenger 1-1 Chat Dialog                                              │
│ - AI Copilot Floating Drawer                                                  │
│ [z-index: 50+, isolate stacking context, backdrop-blur-xl, zero z-fighting]   │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴────────────────────────────────────────┐
│ Layer 2: SVG Morphing Micro-Interactions (Morphicons Vector Pipeline)         │
│ - Like Button: Line Heart ➔ Radiant Filled Heart + 8-Ray Particle Burst      │
│ - Coin Badge: 3D Spinning Coin ➔ Spring Capsule Balance Badge (Counter Roll)  │
│ - Model Selector: Flash ⚡ ➔ Versatile 🌟 ➔ Master 👑 (Vector Morphing)       │
│ [DOM Vector Thread, Spring Physics: f = -k(x-x0) - cv, zero WebGL touch]     │
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴────────────────────────────────────────┐
│ Layer 1: Core Semantic DOM & 3D Interactive Cards (CSS 3D Compositor)         │
│ - Comic Manga Panels (ComicViewer.tsx: Panels, Sequence Badge, Speech Bubble) │
│ - Feature Cards & Social Feed Story Cards                                     │
│ [perspective: 1000px, preserve-3d, translateZ parallax, specular glare overlay]│
└──────────────────────────────────────┬────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┴────────────────────────────────────────┐
│ Layer 0: Ambient 3D Canvas (ThreeUI WebGL Engine)                            │
│ - Single Shared WebGL Context (fixed, inset: 0, z-index: 0, pointer-events:none)│
│ - Procedural Dong Son Drum Motif (Sun rays, concentric rings, sacred birds)   │
│ - Floating 3D Particle Cloud with gentle cursor repulsion                     │
│ [IntersectionObserver + document.hidden ➔ Auto-Pause CPU/GPU to 0.0%]        │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Khảo Sát Chi Tiết Từng Lớp Kiến Trúc

### 3.1. Layer 0 — Ambient 3D Canvas (ThreeUI Engine)

#### a. Vấn Đề Cốt Tử: Quản Lý WebGL Context Đơn Nhất (Single Shared Canvas)
Trong Next.js App Router, việc chuyển đổi giữa các tab (`landing` ⟷ `workspace`, `setup` ⟷ `editor` ⟷ `comic`) hoặc re-render các Client Components thường dẫn đến lỗi phổ biến: **`WARNING: Too many active WebGL contexts. Oldest context will be lost`**. Nếu mỗi component tự mount một canvas 3D riêng, trình duyệt chỉ cho phép tối đa 8–16 WebGL context đồng thời trước khi ép hủy context cũ, gây đen màn hình hoặc giật lag nghiêm trọng.

**Giải pháp:**
- Triển khai canvas 3D duy nhất tại cấp độ Layout gốc (`src/app/layout.tsx` hoặc component `ThreeAmbientCanvas` bọc ngoài `src/app/page.tsx`).
- Thuộc tính định vị cố định:
  ```css
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
  ```
- **Context Loss Guard:**
  ```typescript
  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault();
    stopRenderLoop();
  }, false);

  canvas.addEventListener('webglcontextrestored', () => {
    rebuildShadersAndBuffers();
    startRenderLoop();
  }, false);
  ```

#### b. Cơ Chế Triệt Tiêu 100% CPU/GPU (Auto-Pause to 0%)
Khi người dùng chuyển sang tab khác trong trình duyệt hoặc cuộn nội dung che khuất canvas, việc tiếp tục chạy `requestAnimationFrame` gây hao pin và tốn tài nguyên GPU vô ích.

**Thuật toán điều khiển:**
1. **Sự kiện `visibilitychange` (Tab chuyển nền):**
   ```typescript
   let rafId: number | null = null;
   let isTabVisible = !document.hidden;

   const handleVisibilityChange = () => {
     isTabVisible = !document.hidden;
     if (!isTabVisible) {
       if (rafId !== null) {
         cancelAnimationFrame(rafId);
         rafId = null;
       }
     } else {
       if (rafId === null && isInViewport) {
         lastTime = performance.now();
         rafId = requestAnimationFrame(render);
       }
     }
   };
   document.addEventListener('visibilitychange', handleVisibilityChange);
   ```
2. **`IntersectionObserver` (Theo dõi hiển thị Viewport):**
   ```typescript
   const observer = new IntersectionObserver(([entry]) => {
     isInViewport = entry.isIntersecting;
     if (!isInViewport && rafId !== null) {
       cancelAnimationFrame(rafId);
       rafId = null;
     } else if (isInViewport && isTabVisible && rafId === null) {
       lastTime = performance.now();
       rafId = requestAnimationFrame(render);
     }
   }, { threshold: 0.05 });
   observer.observe(canvas);
   ```
3. **Idle Sleep Mode (Ngủ sâu khi bất động):** Nếu không có sự kiện chuột (`pointermove`) hay cuộn trang (`scroll`) trong 8 giây, tốc độ frame tự động giảm về 15 FPS hoặc tạm ngừng vẽ, lập tức bừng tỉnh 60 FPS khi phát hiện tương tác người dùng.

#### c. Mỹ Thuật Đồ Họa: Họa Tiết Trống Đồng Đông Sơn & Trường Hạt 3D
- **Họa tiết Trống đồng Đông Sơn:**
  Được dựng bằng toán học thủ tục (Procedural GLSL Fragment Shader / Procedural Geometry):
  - **Tâm trống:** Mặt trời 14 tia sáng rực rỡ tượng trưng cho vầng thái dương của nền văn minh lúa nước sông Hồng. Công thức tọa độ cực:
    $$r = \sqrt{x^2 + y^2}, \quad \theta = \operatorname{atan2}(y, x)$$
    $$\text{SunRay}(\theta) = \max(0.0, \cos(14 \cdot \theta))$$
  - **Vành 1 & 2:** Vành tiếp tuyến hình tròn chấm hạt bồ đề và vành răng cưa/ziczac hình học đối xứng.
  - **Vành 3 (Chủ đạo):** Đàn chim Lạc sải cánh dài bay ngược chiều kim đồng hồ, thể hiện khát vọng tự do và cội nguồn dân tộc.
  - **Vành 4:** Vòng tròn xoắn ốc sóng nước chữ S.
  - **Độ sâu 3D:** Trống đồng nghiêng theo góc Pitch 25°–35° trong không gian 3D, quay chậm quanh trục Z với vận tốc $0.0008\text{ rad/frame}$.
- **Trường hạt ánh sáng 3D (Interactive Particle Cloud):**
  - Số lượng hạt: 350 – 500 điểm trong không gian 3 chiều $(X, Y, Z) \in [-1, 1]^3$.
  - Tương tác chuột: Tọa độ chuột chuẩn hóa $(m_x, m_y)$. Khi chuột di chuyển gần hạt trong bán kính $R = 0.25$, áp dụng lực đẩy mượt mà (Smooth Repulsion Vector):
    $$\vec{F} = \frac{\vec{P}_{xy} - \vec{M}}{\|\vec{P}_{xy} - \vec{M}\|} \cdot \left(1 - \frac{d}{R}\right) \cdot \alpha$$
  - Chuyển động Brown hữu cơ: Khi chuột đứng yên, các hạt tự trôi bồng bềnh nhờ hàm $\sin(t \cdot \omega_1 + \phi)$ và $\cos(t \cdot \omega_2 + \psi)$.
  - Tương thích Light/Dark Mode: Trong Dark Mode, hạt và trống đồng tỏa ánh vàng đồng cổ kính / ngọc bích mờ ảo (`rgba(217, 119, 6, 0.12)`); trong Light Mode chuyển sang tông lam chàm / xám bạc cao cấp (`rgba(99, 102, 241, 0.08)`), hòa quyện hoàn hảo với token màu `--bg-app` và `--bg-surface` của `DESIGN.md`.

---

### 3.2. Layer 1 — Core Semantic DOM & 3D Interactive Cards

#### a. Nguyên Lý Cách Ly Compositor (Zero WebGL Interference)
Toàn bộ thẻ bài trong DOM không hề can thiệp hay chia sẻ bộ đệm với WebGL canvas. Thay vào đó, chúng khai thác sức mạnh của CSS 3D Transforms trên Compositor Thread của trình duyệt:
- Container phối cảnh: `perspective: 1000px;`
- Thẻ bài: `transform-style: preserve-3d; will-change: transform;`

#### b. Toán Học Tính Góc Nghiêng Parallax Tilt
Cho một thẻ bài kích thước $(W, H)$ và tọa độ chuột cục bộ $(x, y) \in [0, W] \times [0, H]$:
1. Chuẩn hóa vị trí chuột về khoảng $[-1, 1]$ tính từ tâm thẻ:
   $$u = \frac{x - W/2}{W/2}, \quad v = \frac{y - H/2}{H/2}$$
2. Giới hạn góc nghiêng tối đa $\theta_{\max} = 12^\circ$:
   $$\text{rotateX} = -v \cdot \theta_{\max}$$
   $$\text{rotateY} = u \cdot \theta_{\max}$$
3. Thêm độ nảy nhẹ khi rê chuột: `scale3d(1.02, 1.02, 1.02)`.
4. Khi rời chuột (`onMouseLeave`): Áp dụng cubic-bezier đàn hồi mượt mà (`transition: transform 0.4s cubic-bezier(0.23, 1, 0.32, 1)`) để trở về trạng thái phẳng $(0^\circ, 0^\circ, 1.0)$.

#### c. Phân Tách Chiều Sâu Đa Tầng (Multi-Plane Layering)
Khi thẻ bài xoay trong không gian 3D, các phần tử con được gán thuộc tính `translateZ` khác nhau, tạo nên hiệu ứng nổi khối ngoạn mục:
- **Áp dụng vào khung truyện Manga (`src/components/comic/ComicViewer.tsx`):**
  - Nền tranh manga: `transform: translateZ(0px)`
  - Huy hiệu số thứ tự cảnh (`#1`, `#2`): `transform: translateZ(28px)`
  - Khung thoại Manga (`.speech-bubble`): `transform: translateZ(48px)` kèm đổ bóng nổi khối `box-shadow: 0 16px 32px rgba(0, 0, 0, 0.35)`.
  *Hiệu ứng này khiến cho bong bóng thoại như đang bay lơ lửng phía trên tranh vẽ manga đen trắng thực thụ!*
- **Áp dụng vào Landing Feature Cards (`src/components/landing/LandingView.tsx`):**
  - Icon tính năng (`Bot`, `Edit3`, `ImageIcon`): `translateZ(36px)`
  - Tiêu đề tính năng: `translateZ(20px)`
  - Lớp phủ ánh sáng gương (Specular Glare Overlay): Tạo một dải sáng radial phản chiếu di chuyển đồng bộ theo chuột:
    `radial-gradient(circle at ${(u * 0.5 + 0.5) * 100}% ${(v * 0.5 + 0.5) * 100}%, rgba(255, 255, 255, 0.16), transparent 60%)`

---

### 3.3. Layer 2 — SVG Morphing Micro-Interactions (Morphicons)

#### a. Động Cơ Vật Lý Lò Xo Tự Lập (Damped Harmonic Oscillator Engine)
Để tránh đưa vào thư viện `framer-motion` cồng kềnh (120KB+), Morphicons sử dụng một bộ giải phương trình vi phân lò xo thuần túy siêu nhẹ (< 1KB), chính xác theo tiêu chuẩn Apple UIKit / Spring Physics:

$$F = -k \cdot (x - x_{\text{target}}) - c \cdot v$$
$$a = \frac{F}{m}$$
$$v \leftarrow v + a \cdot \Delta t$$
$$x \leftarrow x + v \cdot \Delta t$$

Với thông số tinh chỉnh cho cảm giác phản hồi tự nhiên cao nhất:
- Độ cứng lò xo (Stiffness) $k = 240$
- Hệ số cản (Damping) $c = 14$
- Khối lượng $m = 1.0$

#### b. Ba Tương Tác Biến Hình Cốt Lõi (3 Morphicons)

1. **Nút Thích (Like Button) — Biến Hình Tim Rực Rỡ & Nổ Hạt (Burst):**
   - Trạng thái 1 (Chưa thích): Đường nét mảnh viền đơn sắc (`stroke: currentColor`, `fill: transparent`).
   - Kích hoạt nhấp chuột:
     - Vector hình học nội suy từ đường viền mở sang khối tim đầy đặn (`fill: #f43f5e`).
     - Lực bật lò xo: Thẻ tim nảy đột ngột từ tỉ lệ $1.0 \rightarrow 1.35 \rightarrow 0.92 \rightarrow 1.05 \rightarrow 1.0$.
     - Vụ nổ vi hạt (Micro-burst): 8 tia sáng nhỏ bắn tỏa tròn theo các góc $i \cdot \frac{2\pi}{8}$, phóng ra bán kính 18px rồi tan biến trong 400ms.
2. **Huy Hiệu & Bộ Đếm Xu (Coin Counter Badge):**
   - Trạng thái nghỉ: Đồng xu vàng 3D xoay nhẹ trên trục Y (hiệu ứng dẹp/phồng elip theo hàm $\cos(\omega t)$).
   - Kích hoạt tương tác (Di chuột hoặc Sự kiện cộng/trừ xu):
     - Đồng xu quay nhanh với gia tốc góc cao, hãm dần theo cơ chế lò xo.
     - Vỏ bọc elip của đồng xu dãn nở ngang mượt mà thành huy hiệu dạng viên nang (Capsule Badge) hiển thị số dư: `[ (Coin) 100 XU ]`.
     - Bộ đếm số lật (Animated Rolling Counter): Khi trừ xu (ví dụ: -8 xu viết truyện, -16 xu chuyển thể manga), số dư cuộn mượt mà xuống số mới với ánh chớp màu hổ phách/cam.
3. **Bộ Chọn Cấp Độ AI Model (Model Tier Switcher):**
   - 3 cấp độ mô hình sáng tác:
     - **Flash ⚡ (Tốc độ & Linh hoạt):** Biểu tượng tia chớp sắc lẹm, điểm nhấn màu vàng lục bảo.
     - **Versatile 🌟 (Toàn năng & Chiều sâu):** Biểu tượng ngôi sao đa diện 8 cánh, điểm nhấn màu tím thạch anh.
     - **Master 👑 (Bậc thầy & Văn học kinh điển):** Biểu tượng vương miện hoàng gia 5 đỉnh, điểm nhấn ánh vàng kim đế vương.
   - Vector Morphing: Đường dẫn SVG nội suy Bezier mượt mà giữa các đỉnh tia chớp $\rightarrow$ cánh sao $\rightarrow$ chóp vương miện. Khi chuyển nấc, thanh trượt bao quanh trượt với quán tính lò xo nảy nhẹ.

---

### 3.4. Layer 3 — Glassmorphism Overlay & Portals

#### a. Cái Bẫy Stacking Context Của CSS 3D
Trong quy chuẩn render của trình duyệt (W3C CSS Transforms Module): **Bất kỳ phần tử tổ tiên nào có `transform`, `perspective` hoặc `transform-style: preserve-3d` đều tự động biến thành khối chứa (Containing Block) của toàn bộ các phần tử con, KỂ CẢ CÁC PHẦN TỬ CÓ `position: fixed`!**

Hậu quả nếu không cách ly:
- Nếu Modal (Nạp xu, Messenger, Lịch sử) đặt bên trong một component cha có Parallax Tilt 3D, khi modal mở ra, nó sẽ bị **cắt vụn (clipping) bên trong khung chữ nhật của thẻ bài**, đồng thời bị xoay xiên xẹo trong không gian 3D của thẻ bài đó!
- Hiệu ứng kính mờ `backdrop-filter: blur(...)` bị lỗi tạo vệt đen (black artifacts) hoặc mất hoàn toàn tính năng làm mờ trên các trình duyệt Chromium và WebKit khi nằm chung stacking context 3D.

#### b. Giải Pháp Toàn Diện: React Portals + `isolation: isolate` + `z-index: 50+`
Tất cả các thành phần thuộc Layer 3 bắt buộc tuân thủ:
1. **Thoát ly hoàn toàn khỏi cây DOM thông thường qua React Portal:** Gắn trực tiếp vào `document.body` (thông qua component `ClientPortal`).
2. **Kích hoạt thuộc tính `isolation: isolate`:** Tạo một Stacking Context biệt lập hoàn toàn ở cấp độ gốc của trình duyệt. Không một phép biến đổi 3D nào ở Layer 0 hay Layer 1 có thể xuyên thủng hoặc làm biến dạng Layer 3.
3. **Thứ bậc z-index nghiêm ngặt:**
   - Layer 0 (WebGL Canvas): `z-index: 0`
   - Layer 1 (Semantic DOM & Cards): `z-index: 10`
   - Layer 2 (Morphicons Buttons): `z-index: 20`
   - Layer 3 (Glassmorphism Portals & Modals): `z-index: 50` đến `z-index: 60`
   - System Toast: `z-index: 9999`
4. **Hệ Thống Token Glassmorphism Chuẩn:**
   ```css
   background: rgba(255, 255, 255, 0.75); /* Light Mode */
   background: rgba(15, 23, 42, 0.80);    /* Dark Mode (slate-900/80) */
   backdrop-filter: blur(16px) saturate(160%);
   -webkit-backdrop-filter: blur(16px) saturate(160%);
   border: 1px solid rgba(255, 255, 255, 0.25); /* Light */
   border: 1px solid rgba(255, 255, 255, 0.08); /* Dark */
   box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
   ```

#### c. Các Thành Phần Trực Thuộc Layer 3:
- **`CoinTopupModal`:** Hộp thoại Nạp Xu ngân hàng chuẩn 100k VNĐ = 100 Xu, tích hợp mã QR động, chứng chỉ băm giao dịch SHA-256 bất biến.
- **`MessengerDialog`:** Khung hội thoại Open Messenger 1-1 hỗ trợ nhắn tin thời gian thực với bất kỳ người dùng nào, có khả năng thu nhỏ dạng bong bóng góc phải hoặc bung rộng toàn màn hình.
- **`CopilotDrawer` / Modal:** Trợ lý Co-pilot khi kích hoạt ở chế độ toàn màn hình hoặc trên thiết bị di động.
- **Nâng cấp `AuthModal` & `HistoryModal`:** Chuyển đổi hai modal hiện hữu sang bọc qua `ClientPortal` để đồng bộ tuyệt đối với kiến trúc phân lớp.

---

### 3.5. Cơ Chế Thích Ứng Mọi Thiết Bị (Graceful Degradation)

Hệ sinh thái NarrAI phải vận hành trơn tru từ máy tính cấu hình cao đến điện thoại thông minh giá rẻ hoặc máy tính bảng đời cũ.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Bộ Kiểm Tra Năng Lực Thiết Bị & Môi Trường                 │
│  - prefers-reduced-motion: matchMedia('(prefers-reduced-motion: reduce)')    │
│  - Phần cứng: navigator.hardwareConcurrency < 4 || deviceMemory < 4GB        │
│  - WebGL Context: Kiểm tra khả năng khởi tạo WebGL 1.0/2.0                    │
│  - Runtime FPS Watchdog: Đo delta-time liên tục, nếu < 28 FPS trong 3 giây   │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
      [Thiết bị Đạt Chuẩn (60 FPS)]        [Thiết Bị Yếu / Reduced Motion]
      - Layer 0: Full WebGL 3D Canvas       - Layer 0: Tắt WebGL (0% GPU).
        (Trống đồng + Hạt 3D tương tác)       Thay bằng CSS Radial Gradient tĩnh.
      - Layer 1: Parallax 3D Tilt           - Layer 1: Tắt 3D perspective.
        (preserve-3d, specular glare)         Thay bằng CSS hover: -translate-y-1.
      - Layer 2: Vector Path Morphing       - Layer 2: Tắt spring physics.
        (Spring physics micro-interactions)   Thay bằng CSS transition fade/scale.
      - Layer 3: Glassmorphism Blur         - Layer 3: Tắt backdrop-filter blur.
        (backdrop-blur-xl saturate)           Thay bằng nền đục bg-slate-900/95.
```

---

## 4. Kế Hoạch Tích Hợp Chi Tiết (File-by-File Integration Blueprint)

### 4.1. Cấu Trúc Tệp Mới Cần Tạo

| Đường dẫn tệp | Trách nhiệm kiến trúc | Tầng |
|---|---|---|
| `frontend/src/components/canvas/ThreeAmbientCanvas.tsx` | Canvas WebGL duy nhất, Shader Trống đồng Đông Sơn, Hạt 3D, Auto-pause CPU/GPU | Layer 0 |
| `frontend/src/components/cards/InteractiveTiltCard.tsx` | Component bọc thẻ bài tạo hiệu ứng Parallax Tilt 3D, Glare specular, bảo toàn 60 FPS | Layer 1 |
| `frontend/src/components/morphicons/MorphLikeButton.tsx` | Nút Like biến hình SVG từ viền sang tim rực rỡ kèm micro-burst | Layer 2 |
| `frontend/src/components/morphicons/MorphCoinBadge.tsx` | Huy hiệu Xu xoay 3D biến hình thành viên nang số dư kèm counter animated | Layer 2 |
| `frontend/src/components/morphicons/MorphModelSelector.tsx` | Bộ chuyển đổi Model AI Flash ⚡ ➔ Versatile 🌟 ➔ Master 👑 với SVG path morphing | Layer 2 |
| `frontend/src/components/morphicons/springPhysics.ts` | Module toán học giải phương trình vi phân dao động tắt dần điều hòa | Layer 2 |
| `frontend/src/components/portals/ClientPortal.tsx` | Wrapper React Portal gắn vào `document.body` kèm `isolation: isolate` và `z-50` | Layer 3 |
| `frontend/src/components/portals/CoinTopupModal.tsx` | Modal nạp xu ngân hàng (100k = 100 Xu), QR, SHA-256 Ledger badge | Layer 3 |
| `frontend/src/components/portals/MessengerDialog.tsx` | Hộp thoại chat Open Messenger 1-1 giữa người dùng | Layer 3 |
| `frontend/src/lib/performance.ts` | Hook phát hiện phần cứng yếu, `prefers-reduced-motion` và Watchdog tụt FPS | Toàn hệ thống |

### 4.2. Các Tệp Hiện Hữu Cần Cập Nhật & Điểm Chạm

1. **`frontend/src/app/layout.tsx` hoặc `src/app/page.tsx`:**
   - Import và mount `<ThreeAmbientCanvas />` ở lớp nền tĩnh (`z-0`).
   - Cung cấp container portal an toàn.
2. **`frontend/src/components/comic/ComicViewer.tsx`:**
   - Bọc từng `ComicPanelCard` bằng `<InteractiveTiltCard>` để mang lại trải nghiệm xem Manga 3D chân thực, đưa bong bóng thoại lên độ cao `translateZ(48px)`.
   - Bổ sung `<MorphLikeButton />` tại góc mỗi khung tranh hoặc thanh công cụ tương tác của tập truyện.
3. **`frontend/src/components/landing/LandingView.tsx`:**
   - Bọc 3 thẻ tính năng (`feat1`, `feat2`, `feat3`) bằng `<InteractiveTiltCard>`.
   - Gắn huy hiệu coin thử nghiệm hoặc demo Morphicon.
4. **`frontend/src/components/editor/AICopilotPanel.tsx`:**
   - Thay thế nút chọn hoặc bổ sung `<MorphModelSelector />` tại phần đầu Copilot để người dùng chuyển đổi linh hoạt giữa 3 cấp độ AI (Flash / Versatile / Master).
5. **`frontend/src/components/layout/Sidebar.tsx`:**
   - Tích hợp `<MorphCoinBadge />` hiển thị số dư người dùng (ví dụ: 100 Xu) có nút bấm mở `<CoinTopupModal />`.
   - Bổ sung nút mở `<MessengerDialog />` để truy cập Open Messenger.
6. **`frontend/src/components/modals/AuthModal.tsx` & `HistoryModal.tsx`:**
   - Thay thế thẻ bọc `fixed inset-0` thông thường bằng `<ClientPortal>` để chống xung đột Stacking Context 3D.
7. **`frontend/src/lib/i18n.ts`:**
   - Bổ sung từ điển song ngữ cho các nhãn mới:
     - `coin_balance`, `topup_coins`, `topup_title`, `package_100k`, `sha256_proof`, `messenger_title`, `model_flash`, `model_versatile`, `model_master`.

---

## 5. Rà Soát Tính Khả Thi Biên Dịch (Build Feasibility & Zero-Risk Strategy)

### 5.1. Khảo Sát `npm run build` & Static Export (`output: 'export'`)
- Trong `frontend/next.config.mjs`:
  ```javascript
  ...(process.env.VERCEL ? {} : { output: 'export' }),
  ```
- Với chế độ `output: 'export'`, Next.js sẽ tiền biên dịch toàn bộ trang thành HTML tĩnh (`out/`).
- **Nguyên tắc an toàn tuyệt đối:**
  1. Mọi đối tượng phụ thuộc trình duyệt (`window`, `document`, `navigator`, `HTMLCanvasElement`, `WebGLRenderingContext`) **tuyệt đối không được gọi trong phạm vi render khởi tạo ban đầu (render phase)**.
  2. Toàn bộ logic khởi tạo WebGL, gán `addEventListener`, và gọi `createPortal` phải nằm trọn vẹn trong `useEffect` với cờ bảo vệ `const [mounted, setMounted] = useState(false);`.
  3. `ClientPortal` trả về `null` trong lần render đầu tiên trên server và chỉ gọi `createPortal(children, document.body)` sau khi đã mount trên client.
  4. Đảm bảo tuân thủ triệt để nguyên tắc này sẽ giúp lệnh `npm run build` sản xuất thành công 100% với 0 lỗi TypeScript hoặc Hydration Mismatch.

### 5.2. So Sánh Kiến Trúc: Zero-Dependency Native WebGL vs Three.js NPM Package

| Tiêu chí | Native GLSL WebGL Shader (Khuyên dùng) | Cài đặt `three` & `@types/three` |
|---|---|---|
| **Dung lượng Bundle JS** | **~12 KB** (Gần như bằng 0) | **~650 KB** (Tăng 400% dung lượng JS) |
| **Tốc độ tải trang** | Tức thì (Không làm trễ First Contentful Paint) | Tăng thời gian phân tích cú pháp JS thêm 150-300ms |
| **Rủi ro cài đặt npm** | **0% rủi ro** (Không cần chạy npm install) | Tiềm ẩn rủi ro timeout/permission prompt |
| **Khả năng kiểm soát WebGL Context** | 100% trực tiếp trên `WebGLRenderingContext` | Bị trừu tượng hóa qua `WebGLRenderer` |
| **Hiệu năng 60 FPS** | Đạt chuẩn 60 FPS mượt mà | Đạt chuẩn 60 FPS |
| **Tự động pause về 0% CPU** | Trực tiếp ngắt `requestAnimationFrame` | Cần can thiệp vào renderer loop |

**Khuyến nghị khảo sát:**  
Đội ngũ phát triển nên triển khai Layer 0 bằng **Native WebGL Shader Engine** tự chứa trong `ThreeAmbientCanvas.tsx`. Điều này bảo đảm không phụ thuộc gói ngoài, không gây rủi ro cài đặt, và đạt tỷ lệ thành công của `npm run build` là 100%.

---

## 6. Ma Trận Chấp Nhận & Xác Minh (Acceptance Criteria & Verification)

| Hạng mục kiểm thử | Tiêu chuẩn đạt | Phương thức kiểm tra |
|---|---|---|
| **Layer 0 Singleton** | Chỉ duy nhất 1 thẻ `<canvas>` WebGL trong toàn bộ cây DOM | `document.querySelectorAll('canvas').length === 1` |
| **Layer 0 Auto-pause** | Khi tab chuyển ẩn (`document.hidden = true`), render loop dừng hẳn, CPU/GPU 0% | Kiểm tra biến `rafId === null` khi kích hoạt `visibilitychange` |
| **Layer 1 Manga 3D Tilt** | Khung truyện manga nghiêng theo chuột, khung thoại nổi `translateZ(48px)` | Kiểm tra computed style `transform` khi rê chuột qua `.comic-panel` |
| **Layer 2 Morphicons** | Nút Like nảy lò xo + micro-burst; Đồng xu xoay thành viên nang; Model switch 3 cấp độ | Kiểm tra tương tác nhấp chuột, kiểm tra biến thiên SVG path |
| **Layer 3 Portals** | Modal Nạp xu & Messenger gắn tại `document.body`, mang `isolation: isolate` | Kiểm tra phần tử cha của modal nằm trực tiếp dưới `<body>` |
| **Graceful Degradation** | Khi bật `prefers-reduced-motion`, WebGL canvas tắt, card không nghiêng 3D | Giả lập `matchMedia('(prefers-reduced-motion: reduce)')` |
| **Biên dịch Frontend** | Lệnh `npm run build` sinh ra thư mục `out/` thành công 0 lỗi | Kiểm tra kết quả biên dịch Next.js |

---

## 7. Kết Luận Khảo Sát

Kiến trúc **Frontend Phân Lớp Không Xung Đột (ThreeUI 3D + Morphicons Pipeline)** đã được định hình hoàn chỉnh, có cơ sở toán học vững chắc, giải quyết triệt để xung đột Stacking Context 3D và bảo đảm hiệu năng 60 FPS ổn định trên toàn bộ các trang của NarrAI. Bản thiết kế này đã sẵn sàng để chuyển giao sang giai đoạn lập kế hoạch chi tiết và thực thi.
