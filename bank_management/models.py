# Add this to your existing models.py file

class CibilScore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cibil_score')
    score = models.IntegerField(default=0)
    payment_history_score = models.IntegerField(default=0)
    credit_utilization_score = models.IntegerField(default=0)
    credit_history_score = models.IntegerField(default=0)
    credit_mix_score = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s CIBIL Score: {self.score}"
    
    @property
    def payment_history_percentage(self):
        return (self.payment_history_score / 315) * 100
        
    @property
    def credit_utilization_percentage(self):
        return (self.credit_utilization_score / 270) * 100
        
    @property
    def credit_history_percentage(self):
        return (self.credit_history_score / 135) * 100
        
    @property
    def credit_mix_percentage(self):
        return (self.credit_mix_score / 180) * 100
        
    @property
    def category(self):
        if self.score >= 750:
            return "Excellent"
        elif self.score >= 700:
            return "Good"
        elif self.score >= 650:
            return "Fair"
        elif self.score >= 600:
            return "Poor"
        else:
            return "Very Poor"


class CibilScoreHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cibil_score_history')
    score = models.IntegerField()
    payment_history_score = models.IntegerField()
    credit_utilization_score = models.IntegerField()
    credit_history_score = models.IntegerField()
    credit_mix_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
