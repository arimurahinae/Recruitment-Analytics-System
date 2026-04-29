from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    comp_compId = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="公司ID")
    comp_compIndustry = models.CharField(max_length=255, blank=True, verbose_name="公司行业")
    comp_compLogo = models.URLField(max_length=500, blank=True, verbose_name="公司Logo")
    comp_compName = models.CharField(max_length=255, db_index=True, verbose_name="公司名称")
    comp_compScale = models.CharField(max_length=100, blank=True, verbose_name="公司规模")
    comp_compStage = models.CharField(max_length=100, blank=True, verbose_name="融资阶段")
    comp_link = models.URLField(max_length=500, blank=True, verbose_name="公司链接")

    class Meta:
        db_table = "job_company"
        verbose_name = "公司"
        verbose_name_plural = "公司"
        indexes = [
            models.Index(fields=["comp_compName"], name="idx_company_name"),
            models.Index(fields=["comp_compIndustry"], name="idx_company_industry"),
        ]

    def __str__(self):
        return self.comp_compName or self.comp_compId


class Recruiter(TimeStampedModel):
    recruiter_recruiterId = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="招聘者ID")
    recruiter_chatted = models.BooleanField(default=False, verbose_name="是否已沟通")
    recruiter_imId = models.CharField(max_length=64, blank=True, db_index=True, verbose_name="IM ID")
    recruiter_imShowText = models.CharField(max_length=255, blank=True, verbose_name="IM展示文案")
    recruiter_imStatus = models.IntegerField(null=True, blank=True, verbose_name="IM状态")
    recruiter_imUserType = models.CharField(max_length=50, blank=True, verbose_name="IM用户类型")
    recruiter_inDay = models.IntegerField(null=True, blank=True, verbose_name="活跃天数")
    recruiter_recruiterName = models.CharField(max_length=100, blank=True, verbose_name="招聘者姓名")
    recruiter_recruiterPhoto = models.URLField(max_length=500, blank=True, verbose_name="招聘者头像")
    recruiter_recruiterTitle = models.CharField(max_length=255, blank=True, verbose_name="招聘者职位")

    class Meta:
        db_table = "job_recruiter"
        verbose_name = "招聘者"
        verbose_name_plural = "招聘者"
        indexes = [
            models.Index(fields=["recruiter_recruiterName"], name="idx_recruiter_name"),
            models.Index(fields=["recruiter_imId"], name="idx_recruiter_imid"),
        ]

    def __str__(self):
        return self.recruiter_recruiterName or self.recruiter_recruiterId


class Job(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobs",
        verbose_name="公司",
    )
    recruiter = models.ForeignKey(
        Recruiter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobs",
        verbose_name="招聘者",
    )

    dataInfo = models.JSONField(null=True, blank=True, verbose_name="原始dataInfo")
    dataParams = models.JSONField(null=True, blank=True, verbose_name="原始dataParams")
    job_advViewFlag = models.IntegerField(null=True, blank=True, verbose_name="广告展示标识")
    job_campusJobKind = models.CharField(max_length=100, blank=True, verbose_name="校招类型")
    job_dataPromId = models.CharField(max_length=100, blank=True, verbose_name="推广ID")
    job_dq = models.CharField(max_length=100, blank=True, db_index=True, verbose_name="工作地点")
    job_g = models.CharField(max_length=255, blank=True, verbose_name="job_g")
    job_h5OuterLink = models.URLField(max_length=500, blank=True, verbose_name="H5外链")
    job_j = models.TextField(blank=True, verbose_name="岗位描述")
    job_jobId = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="岗位ID")
    job_jobKind = models.CharField(max_length=100, blank=True, verbose_name="岗位类型")
    job_labels = models.TextField(blank=True, verbose_name="岗位标签")
    job_link = models.URLField(max_length=500, blank=True, verbose_name="岗位链接")
    job_pcOuterLink = models.URLField(max_length=500, blank=True, verbose_name="PC外链")
    job_refreshTime = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="刷新时间")
    job_requireEduLevel = models.CharField(max_length=100, blank=True, verbose_name="学历要求")
    job_requireWorkYears = models.CharField(max_length=100, blank=True, verbose_name="工作年限")
    job_salary = models.CharField(max_length=100, blank=True, db_index=True, verbose_name="薪资文本")
    salary_min = models.IntegerField(null=True, blank=True, db_index=True, verbose_name="最低薪资(K)")
    salary_max = models.IntegerField(null=True, blank=True, db_index=True, verbose_name="最高薪资(K)")
    job_title = models.CharField(max_length=255, db_index=True, verbose_name="岗位标题")
    job_topJob = models.BooleanField(default=False, db_index=True, verbose_name="是否置顶")
    query_city_code = models.CharField(max_length=32, blank=True, db_index=True, verbose_name="城市编码")
    query_city_dq_code = models.CharField(max_length=32, blank=True, db_index=True, verbose_name="城市地区编码")
    query_city_name = models.CharField(max_length=100, blank=True, db_index=True, verbose_name="城市名称")

    class Meta:
        db_table = "job_job"
        verbose_name = "岗位"
        verbose_name_plural = "岗位"
        indexes = [
            models.Index(fields=["job_title"], name="idx_job_title"),
            models.Index(fields=["query_city_name"], name="idx_job_city_name"),
            models.Index(fields=["query_city_code"], name="idx_job_city_code"),
            models.Index(fields=["salary_min", "salary_max"], name="idx_job_salary_range"),
            models.Index(fields=["job_refreshTime"], name="idx_job_refresh_time"),
            models.Index(fields=["job_topJob"], name="idx_job_top"),
        ]

    def __str__(self):
        return f"{self.job_title}({self.job_jobId})"
