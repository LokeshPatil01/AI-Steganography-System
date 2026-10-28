"""Image loading, validation, and lossless format conversion module."""
import io
from typing import Tuple, Union
import numpy as np
from PIL import Image

class ImageValidationError(Exception):
    """Raised when an image fails format, dimension, or color space validation."""
    pass

class ImageLoader:
    """Validates and loads images into NumPy RGB pixel arrays."""

    MIN_DIMENSION = 32
    MAX_DIMENSION = 4096
    SUPPORTED_FORMATS = {"PNG"}

    @classmethod
    def load_image(cls, image_source: Union[bytes, str, io.BytesIO]) -> Tuple[np.ndarray, Tuple[int, int]]:
        """Loads an image source, validates its integrity and dimensions,
        and returns a NumPy uint8 RGB array of shape (H, W, 3).

        Args:
            image_source: Image file bytes, file path, or BytesIO buffer.

        Returns:
            Tuple of (pixel_array: np.ndarray, (width, height): Tuple[int, int])
        """
        try:
            if isinstance(image_source, bytes):
                img = Image.open(io.BytesIO(image_source))
            elif isinstance(image_source, io.BytesIO):
                img = Image.open(image_source)
            elif isinstance(image_source, str):
                img = Image.open(image_source)
            else:
                raise ImageValidationError("Unsupported image source type.")

            # Validate format (Lossless PNG required for spatial steganography)
            img_format = img.format
            if img_format and img_format.upper() not in cls.SUPPORTED_FORMATS:
                raise ImageValidationError(
                    f"Unsupported image format: '{img_format}'. "
                    f"Only lossless formats ({', '.join(cls.SUPPORTED_FORMATS)}) are supported."
                )

            # Validate dimensions
            width, height = img.size
            if width < cls.MIN_DIMENSION or height < cls.MIN_DIMENSION:
                raise ImageValidationError(
                    f"Image dimensions ({width}x{height}) are smaller than minimum "
                    f"supported size ({cls.MIN_DIMENSION}x{cls.MIN_DIMENSION})."
                )

            if width > cls.MAX_DIMENSION or height > cls.MAX_DIMENSION:
                raise ImageValidationError(
                    f"Image dimensions ({width}x{height}) exceed maximum allowed "
                    f"size ({cls.MAX_DIMENSION}x{cls.MAX_DIMENSION})."
                )

            # Convert to standard RGB (24-bit: 3 channels, 8 bits/channel)
            rgb_img = img.convert("RGB")
            pixel_array = np.array(rgb_img, dtype=np.uint8)

            return pixel_array, (width, height)

        except ImageValidationError:
            raise
        except Exception as e:
            raise ImageValidationError(f"Failed to decode image data: {e}") from e

    @classmethod
    def save_image_to_bytes(cls, pixel_array: np.ndarray) -> bytes:
        """Converts an RGB NumPy array back into lossless PNG bytes."""
        if pixel_array.ndim != 3 or pixel_array.shape[2] != 3:
            raise ImageValidationError("Pixel array must have shape (H, W, 3).")

        img = Image.fromarray(pixel_array.astype(np.uint8), mode="RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=False)
        return buffer.getvalue()
