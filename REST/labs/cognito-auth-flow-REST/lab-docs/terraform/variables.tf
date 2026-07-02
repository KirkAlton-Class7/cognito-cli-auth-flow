# ================================================================
# VARIABLES
# ================================================================

# ----------------------------------------------------------------
# Input Application Name
# ----------------------------------------------------------------

variable "app" {
  type        = string
  description = "Application name (short)"
  default     = "chewbacca-auth-rest" # Update with new application name
}

# ----------------------------------------------------------------
# Input Environment
# ----------------------------------------------------------------

variable "env" {
  type        = string
  default     = "dev"
  description = "Input environment name (dev, test, prod)."

}