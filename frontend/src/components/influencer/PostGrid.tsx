import { Heart, MessageCircle, Play, Image } from 'lucide-react'
import type { Post } from '@/types'
import { formatNumber, proxyImage } from '@/utils/formatters'

interface PostGridProps {
  posts: Post[]
}

export function PostGrid({ posts }: PostGridProps) {
  if (posts.length === 0) {
    return (
      <div className="text-center py-6 text-gray-500 text-sm">No posts available</div>
    )
  }

  return (
    <div className="grid grid-cols-3 gap-2">
      {posts.slice(0, 6).map((post) => (
        <a
          key={post.id}
          href={post.post_url ?? '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="relative aspect-square group overflow-hidden rounded-xl bg-gray-800"
          onClick={(e) => !post.post_url && e.preventDefault()}
        >
          {post.local_thumbnail || post.thumbnail_url ? (
            <img
              src={proxyImage(post.local_thumbnail
                ? `/static/thumbnails/${post.local_thumbnail}`
                : post.thumbnail_url!)}
              alt=""
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
              onError={(e) => {
                const img = e.target as HTMLImageElement
                img.style.display = 'none'
                img.parentElement!.querySelector('.fallback-icon')?.classList.remove('hidden')
              }}
            />
          ) : null}

          <div className="fallback-icon hidden absolute inset-0 flex items-center justify-center">
            <Image size={24} className="text-gray-600" />
          </div>

          {post.is_video && (
            <div className="absolute top-1.5 right-1.5 bg-black/50 rounded-full p-0.5">
              <Play size={10} className="text-white fill-white" />
            </div>
          )}

          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-colors flex items-end">
            <div className="w-full px-2 pb-2 flex gap-3 text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="flex items-center gap-1">
                <Heart size={10} className="fill-white" />
                {formatNumber(post.likes)}
              </span>
              <span className="flex items-center gap-1">
                <MessageCircle size={10} />
                {formatNumber(post.comments)}
              </span>
            </div>
          </div>
        </a>
      ))}
    </div>
  )
}
