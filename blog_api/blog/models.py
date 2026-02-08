from datetime import timezone
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=220, unique=True)
    content = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'blog_article'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author','created_at'], name='idx_article_author_created'),
            models.Index(fields=['status','published_at'], name='idx_article_status_published'),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        #Agar status == published bo'lsa published_at bo'lishi kerak
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        #Agar published bo'lmasa published_atni None qilib qo'yamiz
        if self.status != self.Status.PUBLISHED:
            self.published_at = None

    def save(self, *args, **kwargs):
        # Agar slug bo'sh bo'lib kelsa title`dan generatsiya qilamiz
        if not self.slug:
            base = slugify(self.title)[:210] or 'article'
            slug = base
            i=1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                suffix = f'-{i}'
                slug = f'{base[:220-len(suffix)]}{suffix}'
            self.slug = slug

        #clean()`dagi publish logikasini ishlatamiz
        self.full_clean()
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=64)
    slug = models.CharField(max_length=80, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_tag'
        indexes = [
            models.Index(fields=['name'], name='idx_tag_name'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:80] or 'tag'
        super().save(*args, **kwargs)


class ArticleTag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='article_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='tag_articles')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blog_article_tag'
        constraints = [
            models.UniqueConstraint(fields=['article', 'tag'], name='uq_article_tag'),
        ]
        indexes = [
            models.Index(fields=["tag"], name='idx_article_tag_tag'),
            models.Index(fields=['article'], name='idx_article_tag_article'),
        ]

    def __str__(self):
        return f"{self.article_id} - {self.tag_id}"
