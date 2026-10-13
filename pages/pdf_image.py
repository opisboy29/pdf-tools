
import streamlit as st
import tempfile
import os
import zipfile
from io import BytesIO
from pathlib import Path

from pdf2image import convert_from_path, pdfinfo_from_path

st.set_page_config(
    page_title="PDF to Image",
    page_icon="🖼️",
    layout="centered"
)

# ---------------------------
# Back to Home
# ---------------------------
if st.button("⬅ Kembali ke Halaman Utama"):
    st.switch_page("app.py")

st.markdown("---")
st.title("🖼️ PDF to Image")
st.caption("Convert PDF pages into PNG or JPG images")

# ---------------------------
# Upload PDF
# ---------------------------
uploaded_file = st.file_uploader(
    "Upload PDF file",
    type=["pdf"]
)

# ---------------------------
# Conversion settings
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    image_format = st.selectbox(
        "Image format",
        ["PNG", "JPG"]
    )

with col2:
    dpi = st.selectbox(
        "Image resolution (DPI)",
        [100, 150, 200, 300],
        index=1
    )

st.caption(
    "150 DPI cocok untuk penggunaan umum. "
    "Gunakan 300 DPI untuk gambar yang lebih detail, "
    "dengan kebutuhan memori yang lebih besar."
)

# ---------------------------
# Convert button
# ---------------------------
convert_clicked = st.button(
    "🖼️ Convert PDF to Image",
    use_container_width=True,
    disabled=uploaded_file is None
)

if convert_clicked and uploaded_file is not None:
    try:
        original_name = Path(uploaded_file.name).stem
        extension = "png" if image_format == "PNG" else "jpg"
        output_zip_name = f"{original_name}_images.zip"

        with st.spinner("⏳ Converting PDF pages to images..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                pdf_path = os.path.join(tmpdir, "input.pdf")

                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Read PDF page count
                info = pdfinfo_from_path(pdf_path)
                total_pages = int(info["Pages"])

                if total_pages < 1:
                    raise ValueError("PDF does not contain any pages.")

                # Convert PDF to images
                images = convert_from_path(
                    pdf_path,
                    dpi=dpi,
                    fmt=extension,
                    thread_count=2,
                    grayscale=False
                )

                if not images:
                    raise ValueError(
                        "No images were generated from this PDF."
                    )

                zip_buffer = BytesIO()

                with zipfile.ZipFile(
                    zip_buffer,
                    mode="w",
                    compression=zipfile.ZIP_DEFLATED
                ) as zip_file:

                    for index, image in enumerate(images, start=1):
                        image_buffer = BytesIO()

                        if image_format == "JPG":
                            image = image.convert("RGB")
                            image.save(
                                image_buffer,
                                format="JPEG",
                                quality=95,
                                optimize=True
                            )
                        else:
                            image.save(
                                image_buffer,
                                format="PNG",
                                optimize=True
                            )

                        image_filename = (
                            f"{original_name}_page_{index:02d}.{extension}"
                        )

                        zip_file.writestr(
                            image_filename,
                            image_buffer.getvalue()
                        )

                        image.close()

                zip_bytes = zip_buffer.getvalue()

        # ---------------------------
        # Results
        # ---------------------------
        st.success(
            f"✅ Successfully converted {total_pages} PDF pages!"
        )

        st.write(f"**Original PDF:** {uploaded_file.name}")
        st.write(f"**Image format:** {image_format}")
        st.write(f"**Resolution:** {dpi} DPI")
        st.write(f"**Total images:** {total_pages}")
        st.write(
            f"**ZIP size:** {len(zip_bytes) / 1024 / 1024:.2f} MB"
        )

        st.download_button(
            label="⬇️ Download Images (ZIP)",
            data=zip_bytes,
            file_name=output_zip_name,
            mime="application/zip",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"❌ Conversion failed: {e}")
