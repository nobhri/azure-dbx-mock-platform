variable "prefix"             {
   type = string  
   default = "mock" 
   }
variable "location"           {
   type = string  
   default = "japaneast" 
   }
variable "rg_name"            { 
  type = string  
  default = "rg-mock-data" 
  }
variable "adls_name" { # 3–24 lowercase, globally unique
  type        = string
  description = "ADLS Gen2 account name"
}

variable "landing_container"  { 
  type = string  
  default = "landing" 
  }
variable "uc_root_container"  { 
  type = string  
  default = "uc-root" 
  }
variable "bronze_container"   { 
  type = string  
  default = "bronze" 
  }
variable "silver_container"   { 
  type = string  
  default = "silver" 
  }

variable "workspace_sku"      { 
  type = string  
  default = "premium"
   } # or "trial" etc.
