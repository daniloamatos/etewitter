from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from main.models import Follower, Notification, ReplyRetweet, Replys, Tweet, TweetRetweet
from register.models import Usuario


DEMO_PASSWORD = 'EteDemo2026!'
PORTUGUESE_PROFILES = [
    ('marina', 'Marina Costa', 'Curiosa por tecnologia, livros e boas conversas.', 'tecnologia', 'um protótipo simples já ajuda a testar uma ideia', 'Que ferramenta te ajudou a aprender algo novo?'),
    ('caio', 'Caio Mendes', 'Desenvolvedor web; café e código todos os dias.', 'desenvolvimento web', 'escrever testes antes de publicar evita surpresas', 'Qual projeto pessoal você está construindo?'),
    ('luiza', 'Luiza Alves', 'Fotografia, trilhas e café passado na hora.', 'fotografia e natureza', 'a luz da manhã transforma qualquer passeio', 'Você prefere praia, campo ou cidade?'),
    ('pedro', 'Pedro Lima', 'Designer de produto atento aos pequenos detalhes.', 'design de produto', 'um bom rascunho economiza muitas horas', 'Qual app tem a interface mais clara para você?'),
    ('natalia', 'Natália Rocha', 'Aprendendo, compartilhando e fazendo perguntas.', 'aprendizado contínuo', 'anotar dúvidas deixa o estudo mais objetivo', 'O que você aprendeu nesta semana?'),
    ('rafaelcodes', 'Rafael Nogueira', 'Backend, APIs e sistemas que aguentam crescer.', 'APIs e backend', 'nomes claros deixam as APIs mais fáceis de usar', 'Qual documentação técnica você consulta sempre?'),
    ('brunavieira', 'Bruna Vieira', 'Ilustração digital e histórias em cores.', 'ilustração digital', 'uma paleta curta pode contar uma história inteira', 'Que tema você gostaria de ver numa ilustração?'),
    ('thiagofront', 'Thiago Azevedo', 'Frontend e acessibilidade para todo mundo.', 'acessibilidade na web', 'teclado e leitor de tela também merecem atenção', 'Qual detalhe acessível faz diferença no seu dia?'),
    ('camilaoliveira', 'Camila Oliveira', 'Ciência de dados aplicada a perguntas reais.', 'ciência de dados', 'um gráfico simples costuma revelar padrões', 'Que pergunta você gostaria de responder com dados?'),
    ('joaopedro', 'João Pedro Reis', 'Música independente e produção caseira.', 'produção musical', 'gravar uma ideia logo evita esquecer a melodia', 'Que artista independente você recomenda?'),
    ('isabelamoraes', 'Isabela Moraes', 'Leitura, escrita e clubes de livros.', 'literatura brasileira', 'uma boa conversa muda nossa leitura de um livro', 'Qual livro ficou na sua cabeça por dias?'),
    ('felipematos', 'Felipe Matos', 'Automação residencial e projetos com sensores.', 'eletrônica e automação', 'um sensor barato já rende boas experiências', 'Que tarefa você gostaria de automatizar em casa?'),
    ('caroldesign', 'Carolina Freire', 'Pesquisa com pessoas e design centrado no usuário.', 'pesquisa com usuários', 'ouvir alguém usar o produto ensina muito', 'Qual pergunta você faz numa entrevista de produto?'),
    ('gustavolima', 'Gustavo Lima', 'Corrida de rua, planilhas e metas realistas.', 'corrida de rua', 'constância vale mais que um treino perfeito', 'Qual percurso você gosta de correr?'),
    ('beatrizluz', 'Beatriz Luz', 'Astronomia para curiosos e noites de céu limpo.', 'astronomia', 'olhar para o céu sempre traz uma nova pergunta', 'Você já observou Saturno por um telescópio?'),
    ('ricardosilva', 'Ricardo Silva', 'Privacidade digital e segurança para iniciantes.', 'privacidade digital', 'um gerenciador de senhas facilita bons hábitos', 'Que hábito digital você recomenda aos amigos?'),
    ('amandafarias', 'Amanda Farias', 'Cozinha vegetariana e receitas de poucos passos.', 'cozinha vegetariana', 'temperos frescos deixam o prato mais interessante', 'Qual receita simples você faz durante a semana?'),
    ('lucasferreira', 'Lucas Ferreira', 'Mapas, transporte público e cidades caminháveis.', 'mobilidade urbana', 'calçadas boas tornam o bairro mais próximo', 'O que melhoraria o caminho até o seu trabalho?'),
    ('sofiaramos', 'Sofia Ramos', 'Cinema, fotografia analógica e sessões comentadas.', 'cinema e fotografia', 'um bom filme continua depois dos créditos', 'Qual filme você reassistiria hoje?'),
    ('viniciusbyte', 'Vinícius Prado', 'Software livre e ferramentas feitas em comunidade.', 'software livre', 'contribuições pequenas também mantêm projetos vivos', 'Qual projeto aberto você usa com frequência?'),
    ('helenaart', 'Helena Duarte', 'Museus, desenho de observação e história da arte.', 'história da arte', 'desenhar por alguns minutos muda o jeito de observar', 'Que exposição você gostaria de visitar?'),
    ('danielbarros', 'Daniel Barros', 'Infraestrutura, Linux e curiosidades de redes.', 'Linux e infraestrutura', 'um bom log ajuda a encontrar problemas mais rápido', 'Qual comando você usa todos os dias?'),
    ('larissaweb', 'Larissa Gomes', 'Conteúdo web, escrita clara e boas conversas.', 'escrita para web', 'revisar em voz alta ajuda a cortar palavras sobrando', 'Que texto da internet você guarda para reler?'),
    ('andrepires', 'André Pires', 'Ciclismo, manutenção básica e passeios longos.', 'ciclismo', 'revisar os freios antes de sair é sempre uma boa', 'Qual estrada ou ciclovia você recomenda?'),
    ('marcosvinil', 'Marcos Vinícius', 'Discos usados e música brasileira de todo tipo.', 'música brasileira', 'um lado B às vezes vira a faixa favorita', 'Qual disco você ouviu inteiro recentemente?'),
]
ENGLISH_PROFILES = [
    ('alexmorgan', 'Alex Morgan', 'Product designer who loves clear interfaces.', 'product design', 'a quick sketch can save hours of rework', 'Which app makes a task feel effortless?'),
    ('jamietaylor', 'Jamie Taylor', 'Learning in public, one small project at a time.', 'web development', 'small projects make new ideas easier to test', 'What are you building this month?'),
    ('emilychen', 'Emily Chen', 'Street photography, rainy days, and good coffee.', 'street photography', 'soft light can make an ordinary street feel new', 'What is your favorite place to take a walk?'),
    ('oliverreed', 'Oliver Reed', 'Open source contributor and documentation fan.', 'open source', 'clear examples make a library easier to adopt', 'Which open source tool do you recommend?'),
    ('avaanderson', 'Ava Anderson', 'Books, bookshops, and thoughtful conversations.', 'books and reading', 'a great book gives you someone new to think with', 'What are you reading right now?'),
    ('noahwilson', 'Noah Wilson', 'Running trails and celebrating steady progress.', 'trail running', 'a steady pace beats a perfect plan', 'Where do you like to run on weekends?'),
    ('sophiebrown', 'Sophie Brown', 'Illustration, printmaking, and bright colors.', 'illustration', 'two strong colors can say more than ten', 'What would you like to see illustrated?'),
    ('ethanparker', 'Ethan Parker', 'Making the web friendlier with accessibility.', 'web accessibility', 'keyboard navigation helps more people than you expect', 'What accessibility detail do you notice first?'),
    ('gracelee', 'Grace Lee', 'Data science for useful questions, not vanity.', 'data science', 'a simple chart is often the most useful one', 'What question would you explore with data?'),
    ('liamfoster', 'Liam Foster', 'Home recording and independent music discovery.', 'music production', 'recording a rough idea keeps the energy alive', 'Which independent artist should I hear?'),
    ('zoewright', 'Zoe Wright', 'Curious about astronomy and the night sky.', 'astronomy', 'every clear night gives us a new reason to look up', 'Have you ever seen Saturn through a telescope?'),
    ('lucasgray', 'Lucas Gray', 'Privacy tools and practical security habits.', 'digital privacy', 'a password manager makes safer habits simpler', 'What small security habit do you recommend?'),
    ('hannahgreen', 'Hannah Green', 'Plant-based cooking with everyday ingredients.', 'plant-based cooking', 'fresh herbs can brighten a very simple meal', 'What is your favorite quick dinner?'),
    ('masonclark', 'Mason Clark', 'Maps, walkable neighborhoods, and better transit.', 'urban mobility', 'good sidewalks make a neighborhood feel closer', 'What would improve your daily commute?'),
    ('ellajames', 'Ella James', 'Independent films and post-movie conversations.', 'independent cinema', 'the best films stay with you after the credits', 'Which film would you watch again tonight?'),
    ('arthurcole', 'Arthur Cole', 'Linux, infrastructure, and useful terminal tips.', 'Linux and infrastructure', 'good logs make tricky bugs easier to find', 'Which command do you use every day?'),
    ('rubyturner', 'Ruby Turner', 'Writing online and making complicated ideas clear.', 'technical writing', 'reading a draft aloud reveals what can be cut', 'What article do you keep coming back to?'),
    ('jackmiller', 'Jack Miller', 'Cycling, weekend rides, and basic bike repair.', 'cycling', 'checking the brakes before a ride is always worth it', 'Which local route should I try next?'),
    ('lilyward', 'Lily Ward', 'Museums, sketchbooks, and art history.', 'art history', 'drawing for a few minutes changes how you look', 'Which exhibition would you love to visit?'),
    ('henryscott', 'Henry Scott', 'Building small games and sharing what I learn.', 'indie games', 'one good mechanic can carry a whole game', 'What indie game did you finish recently?'),
    ('chloebaker', 'Chloe Baker', 'Community gardens and plants that thrive indoors.', 'urban gardening', 'watching the window light helps you choose a plant', 'Which plant does well in a shady room?'),
    ('evanross', 'Evan Ross', '3D printing prototypes and fixing everyday things.', '3D printing', 'measuring twice saves a lot of filament', 'What would you like to prototype?'),
    ('miayoung', 'Mia Young', 'Local history, old photographs, and city walks.', 'local history', 'old photographs reveal how a neighborhood changed', 'Which place in your town has changed the most?'),
    ('leoporter', 'Leo Porter', 'Language learning through songs and conversations.', 'languages and culture', 'saying a new phrase out loud helps it stick', 'What word in another language do you love?'),
    ('claraevans', 'Clara Evans', 'Open learning resources and better study routines.', 'open education', 'sharing good resources makes learning more accessible', 'Which free resource helped you learn something?'),
]
PROFILES = PORTUGUESE_PROFILES + ENGLISH_PROFILES


class Command(BaseCommand):
    help = 'Create 25 Portuguese and 25 English sample accounts for local development.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('A carga demonstrativa só pode ser usada com DJANGO_DEBUG=True.')

        now = timezone.now()
        users = {}
        for username, name, bio, *_ in PROFILES:
            user, created = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.test', 'name': name,
                    'usernameinsensitive': username.upper(), 'bio': bio,
                    'is_active': True,
                },
            )
            user.name = name
            user.email = f'{username}@example.test'
            user.usernameinsensitive = username.upper()
            user.bio = bio
            user.is_active = True
            if created or not user.check_password(DEMO_PASSWORD):
                user.set_password(DEMO_PASSWORD)
            user.save()
            users[username] = user

        handles = list(users)
        profile_indexes = {username: index for index, username in enumerate(handles)}
        for index, username in enumerate(handles):
            group_start = (index // 25) * 25
            local_index = index % 25
            for offset in (1, 3, 7):
                Follower.objects.get_or_create(
                    follower=users[username],
                    following=users[handles[group_start + (local_index + offset) % 25]],
                )
        for user in users.values():
            user.followersC = Follower.objects.filter(following=user).count()
            user.followingC = Follower.objects.filter(follower=user).count()
            user.save(update_fields=['followersC', 'followingC'])

        posts = []
        for profile_index, profile in enumerate(PROFILES):
            username, _, _, topic, insight, question = profile
            group_start = (profile_index // 25) * 25
            local_index = profile_index % 25
            mention = handles[group_start + (local_index + 5) % 25]
            if profile_index < 25:
                messages = [
                    f'Hoje estou explorando {topic}. {insight.capitalize()}.',
                    f'Uma ideia para colocar em prática: {insight.capitalize()}.',
                    f'Pergunta para a timeline: {question} @{mention}',
                ]
            else:
                messages = [
                    f"Today I'm exploring {topic}. {insight.capitalize()}.",
                    f'An idea I want to try: {insight.capitalize()}.',
                    f'Question for the timeline: {question} @{mention}',
                ]
            for post_number, body in enumerate(messages, start=1):
                slug = f'demo-{username}-{post_number}'
                post, _ = Tweet.objects.get_or_create(
                    tweetLink=f'{username}/status/{slug}',
                    defaults={'tweetAuthor': users[username], 'tweet': body},
                )
                post.tweetAuthor = users[username]
                post.tweet = body
                post.save()
                publish_date = now - timedelta(hours=(profile_index * 11 + post_number * 3) % 336)
                Tweet.objects.filter(pk=post.pk).update(publishDate=publish_date)
                post.refresh_from_db()
                post.mentions.set([users[mention]] if f'@{mention}' in body else [])
                posts.append((profile_index, post, publish_date))

        replies = []
        for post_index, (profile_index, post, post_date) in enumerate(posts):
            group_start = (profile_index // 25) * 25
            author_index = profile_index % 25
            for reply_number, offset in enumerate((1, 6), start=1):
                replier = users[handles[group_start + (author_index + offset) % 25]]
                if profile_index < 25:
                    answer = 'Vou testar essa ideia também.' if reply_number == 1 else 'Obrigado por compartilhar, gostei do ponto.'
                    body = f'Boa, @{post.tweetAuthor.username}! {answer}'
                else:
                    answer = 'I want to try this idea too.' if reply_number == 1 else 'Thanks for sharing, I like this point.'
                    body = f'Nice one, @{post.tweetAuthor.username}! {answer}'
                slug = f'demo-reply-{post_index}-{reply_number}'
                reply, _ = Replys.objects.get_or_create(
                    replyLink=f'{replier.username}/status/{slug}',
                    defaults={'user': replier, 'tweet': post, 'body': body},
                )
                reply.user = replier
                reply.tweet = post
                reply.body = body
                reply.save()
                reply.mentions.set([post.tweetAuthor])
                reply_date = post_date + timedelta(minutes=reply_number * 17)
                Replys.objects.filter(pk=reply.pk).update(publishDate=reply_date)
                replies.append((post_index, profile_index, reply, reply_date))

                if reply_number == 1 and post_index % 4 == 0:
                    child_user = users[handles[group_start + (author_index + 2) % 25]]
                    child_slug = f'demo-child-{post_index}'
                    child_body = (
                        f'Também gostei, @{replier.username}! Vou acompanhar.'
                        if profile_index < 25 else
                        f'I like it too, @{replier.username}! I will follow along.'
                    )
                    child, _ = Replys.objects.get_or_create(
                        replyLink=f'{child_user.username}/status/{child_slug}',
                        defaults={
                            'user': child_user, 'tweet': post,
                            'body': child_body,
                        },
                    )
                    child.user = child_user
                    child.tweet = post
                    child.body = child_body
                    child.save()
                    child.reply.add(reply)
                    child.mentions.set([replier])
                    child_date = reply_date + timedelta(minutes=12)
                    Replys.objects.filter(pk=child.pk).update(publishDate=child_date)
                    replies.append((post_index, profile_index, child, child_date))

        def notify(recipient, actor, kind, body, link, tweet=None, reply=None, when=None):
            if recipient.pk == actor.pk:
                return
            defaults = {'tweet': tweet, 'reply': reply}
            if when:
                defaults['publishDate'] = when
            Notification.objects.get_or_create(
                user=recipient, actor=actor, notification_type=kind,
                body=body, linkzaocarai=link, defaults=defaults,
            )

        for follow in Follower.objects.filter(
            follower__username__in=handles, following__username__in=handles,
        ).select_related('follower', 'following'):
            follower = follow.follower
            followed = follow.following
            follow_body = (
                f'{follower.name} começou a te seguir'
                if profile_indexes[follower.username] < 25 else
                f'{follower.name} started following you'
            )
            notify(
                followed, follower, 'follow',
                follow_body, f'{follower.username}/',
                when=now - timedelta(minutes=(follower.followingC + followed.followersC) % 1440),
            )

        for post_index, (profile_index, post, post_date) in enumerate(posts):
            group_start = (profile_index // 25) * 25
            local_index = profile_index % 25
            english = profile_index >= 25
            actor_indexes = [group_start + (local_index + offset) % 25 for offset in (2, 4, 8, 11)]
            for actor_index in actor_indexes:
                actor = users[handles[actor_index]]
                post.likes.add(actor)
            post.likec = post.likes.count()
            post.replysC = Replys.objects.filter(tweet=post).count()
            post.save(update_fields=['likec', 'replysC'])

            retweeter = users[handles[group_start + (local_index + 9) % 25]]
            if retweeter.pk == post.tweetAuthor_id:
                retweeter = users[handles[group_start + (local_index + 10) % 25]]
            retweet_date = post_date + timedelta(minutes=43)
            TweetRetweet.objects.get_or_create(
                tweet=post, user=retweeter,
                defaults={'created_at': retweet_date},
            )
            for offset in (2, 8):
                actor = users[handles[group_start + (local_index + offset) % 25]]
                if actor.pk != post.tweetAuthor_id:
                    like_body = f'{actor.name} liked your post' if english else f'{actor.name} curtiu sua publicação'
                    notify(post.tweetAuthor, actor, 'like', like_body, post.tweetLink,
                           tweet=post, when=post_date + timedelta(minutes=offset * 5))
            retweet_body = f'{retweeter.name} reposted your post' if english else f'{retweeter.name} repostou sua publicação'
            notify(post.tweetAuthor, retweeter, 'retweet', retweet_body,
                   post.tweetLink, tweet=post, when=retweet_date)
            for mentioned in post.mentions.all():
                mention_body = (
                    f'{post.tweetAuthor.name} mentioned you in a post'
                    if english else f'{post.tweetAuthor.name} mencionou você em um tweet'
                )
                notify(mentioned, post.tweetAuthor, 'mention',
                       mention_body, post.tweetLink,
                       tweet=post, when=post_date)

        for reply_index, (post_index, profile_index, reply, reply_date) in enumerate(replies):
            group_start = (profile_index // 25) * 25
            local_index = profile_index % 25
            english = profile_index >= 25
            actor = users[handles[group_start + (local_index + 12) % 25]]
            reply.likes.add(actor)
            reply.likec = reply.likes.count()
            reply.replysC = Replys.objects.filter(reply=reply).count()
            reply.save(update_fields=['likec', 'replysC'])
            if reply_index % 3 == 0 and actor.pk != reply.user_id:
                reply_retweeter = users[handles[group_start + (local_index + 14) % 25]]
                if reply_retweeter.pk != reply.user_id:
                    ReplyRetweet.objects.get_or_create(
                        reply=reply, user=reply_retweeter,
                        defaults={'created_at': reply_date + timedelta(minutes=21)},
                    )
            if reply.user_id != reply.tweet.tweetAuthor_id:
                reply_body = (
                    f'{reply.user.name} replied to @{reply.tweet.tweetAuthor.username}'
                    if english else f'{reply.user.name} respondeu a @{reply.tweet.tweetAuthor.username}'
                )
                notify(reply.tweet.tweetAuthor, reply.user, 'reply',
                       reply_body,
                       reply.replyLink, tweet=reply.tweet, reply=reply, when=reply_date)
            for mentioned in reply.mentions.all():
                mention_body = (
                    f'{reply.user.name} mentioned you in a reply'
                    if english else f'{reply.user.name} mencionou você em uma resposta'
                )
                notify(mentioned, reply.user, 'mention',
                       mention_body,
                       reply.replyLink, tweet=reply.tweet, reply=reply, when=reply_date)

        self.stdout.write(self.style.SUCCESS(
            f'Demo pronta: {Usuario.objects.filter(username__in=handles).count()} contas, '
            f'{len(posts)} tweets, {len(replies)} respostas, '
            f'{TweetRetweet.objects.count()} reposts de tweets, '
            f'{ReplyRetweet.objects.count()} reposts de respostas e '
            f'{Notification.objects.filter(user__in=users.values()).count()} notificações.'
        ))
        self.stdout.write(f'Senha comum das contas: {DEMO_PASSWORD}')
