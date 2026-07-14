import torch
import torch.nn.functional as F

def focal_loss(logits, targets, alpha=0.25, gamma=2.0):
    bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    p = torch.sigmoid(logits)
    loss = alpha * (1.0 - p) ** gamma * bce
    return loss.mean()

def wind_alignment_penalty(prob_map, wind_u, wind_v, eps=1e-6):
    """
    prob_map: [B,1,H,W] or [B,H,W]
    wind_u, wind_v: [B,H,W]
    Computes alignment penalty between grad(prob_map) and wind vector field.
    """
    # shape normalize
    if prob_map.dim() == 4:
        prob = prob_map.squeeze(1)          # [B,H,W]
    else:
        prob = prob_map                     # [B,H,W]

    # cast wind to same device and dtype
    wind_u = wind_u.to(prob.device, prob.dtype)
    wind_v = wind_v.to(prob.device, prob.dtype)

    # spatial gradients only
    gy, gx = torch.gradient(prob, dim=(1, 2))   # gy d/dy, gx d/dx

    # stack to vector fields
    grad = torch.stack([gx, gy], dim=1)         # [B,2,H,W]
    wind = torch.stack([wind_u, wind_v], dim=1) # [B,2,H,W]

    # cosine similarity penalty
    dot = (grad * wind).sum(dim=1)              # [B,H,W]
    gnorm = torch.linalg.norm(grad, dim=1) + eps
    wnorm = torch.linalg.norm(wind, dim=1) + eps
    cos = dot / (gnorm * wnorm)                 # [-1,1]
    return (1.0 - cos).mean()
