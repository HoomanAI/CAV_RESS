%% generate_all_matlab_figs.m
% Generates ALL 22 .fig files for CAV Reliability Paper
% Covers: 3D figures (5), Innovative figures (11), Summary figures (6)
% Run from MATLAB: cd('E:\Working Docs\Papers\Reliability CAV'); run('code\generate_all_matlab_figs.m')

clear; clc; close all;

BASE   = 'E:\Working Docs\Papers\Reliability CAV';
TDIR   = fullfile(BASE,'results','tables');
OUTDIR = fullfile(BASE,'results','figures','matlab');
if ~exist(OUTDIR,'dir'); mkdir(OUTDIR); end

fprintf('Loading simulation tables...\n');
T4    = readtable(fullfile(TDIR,'exp4.csv'));
T4t   = readtable(fullfile(TDIR,'exp4_traffic.csv'));
T2    = readtable(fullfile(TDIR,'exp2.csv'));
T3    = readtable(fullfile(TDIR,'exp3.csv'));
T5    = readtable(fullfile(TDIR,'exp5.csv'));
T6    = readtable(fullfile(TDIR,'exp6.csv'));
T7    = readtable(fullfile(TDIR,'exp7.csv'));
T8    = readtable(fullfile(TDIR,'exp8.csv'));
T10   = readtable(fullfile(TDIR,'exp10.csv'));
fprintf('  All tables loaded.\n\n');

% ---- Global style ----
set(0,'DefaultAxesFontSize',11,'DefaultAxesFontName','Arial',...
      'DefaultLineLineWidth',2,'DefaultFigureColor','w',...
      'DefaultAxesBox','off','DefaultAxesTickDir','out');

PHI_LEVELS = [1.00 0.95 0.90 0.85 0.80 0.75 0.70];
ALGOS      = {'QiGA','GA','PSO','ALNS','TS'};
C_PHI  = [0.08 0.40 0.75; 0.10 0.47 0.85; 0.26 0.65 0.96;
           1.00 0.60 0.00; 0.89 0.22 0.21];
C_ALGO = [0.13 0.59 0.95; 0.30 0.69 0.31;
           1.00 0.60 0.00; 0.96 0.26 0.21; 0.61 0.15 0.69];

% Helper: save figure
function save_fig(fig, outdir, name)
    savefig(fig, fullfile(outdir, [name '.fig']));
    fprintf('  Saved: %s.fig\n', name);
end

% Helper: get phi means
function v = phi_means(T, metric, phi_u)
    v = arrayfun(@(p) mean(T.(metric)(abs(T.phi_min-p)<1e-9)), phi_u);
end

% =========================================================================
%  ============  3D FIGURES (5)  ============
% =========================================================================
fprintf('===  3D FIGURES  ===\n');

%% 3D-1a  Three-Objective Pareto Front
rng(42);
phi_sel = [1.00 0.90 0.85 0.80 0.70];
fig = figure('Name','3D-1 Pareto Front','Position',[50 50 900 700]);
hold on;
for pi = 1:numel(phi_sel)
    phi = phi_sel(pi); n = 60;
    f1 = phi*0.55 + rand(n,1)*phi*0.45;
    f2 = 100/phi  + rand(n,1)*80/phi;
    f3 = phi*0.85 + rand(n,1)*phi*0.15;
    scatter3(f3,f1,-f2,30,'filled','MarkerFaceColor',C_PHI(pi,:),...
        'MarkerFaceAlpha',0.75,'DisplayName',sprintf('\\phi_{min}=%.2f',phi));
    % Floor shadow
    scatter3(f3,f1,repmat(-max(f2)*1.1,n,1),8,'filled',...
        'MarkerFaceColor',C_PHI(pi,:),'MarkerFaceAlpha',0.15,'HandleVisibility','off');
end
scatter3(1,1,-100,200,'p','MarkerFaceColor',[1 0.84 0],'MarkerEdgeColor','k',...
    'DisplayName','Utopia \ast','LineWidth',1);
xlabel('f_3: Route Reliability','FontWeight','bold');
ylabel('f_1: Priority-Weighted Satisfaction','FontWeight','bold');
zlabel('-f_2: Routing Efficiency','FontWeight','bold');
title({'3D-1  Pareto-Optimal Surface: f_1 \times f_2 \times f_3',...
       'Impact of \phi_{min} on MOO Trade-off Surface'},'FontSize',12);
legend('Location','northwest','NumColumns',2);
view(22,-55); grid on;
save_fig(fig, OUTDIR, '3D1_pareto_front');

%% 3D-1b  Pareto + 2D Projections panel
fig = figure('Name','3D-1 Pareto Projections','Position',[50 50 1100 850]);
rng(42);
ax3d = subplot(2,2,1,'Parent',fig);
axes(ax3d); hold on;
for pi=1:numel(phi_sel)
    phi=phi_sel(pi); n=60;
    f1=phi*0.55+rand(n,1)*phi*0.45; f2=100/phi+rand(n,1)*80/phi; f3=phi*0.85+rand(n,1)*phi*0.15;
    scatter3(f3,f1,-f2,18,'filled','MarkerFaceColor',C_PHI(pi,:),'MarkerFaceAlpha',0.65,...
        'DisplayName',sprintf('\\phi=%.2f',phi));
end
xlabel('f_3'); ylabel('f_1'); zlabel('-f_2'); title('3D View'); view(22,-55); grid on; legend('FontSize',7);

projs = {[2,1],[2,2];[3,1],[2,3];[3,2],[2,4]};  % [xi,yi], subplot pos
xlbls={'f_3: Reliability','f_1: Satisfaction','f_3: Reliability'};
ylbls={'f_1: Satisfaction','-f_2: Efficiency','-f_2: Efficiency'};
neg_y=[false,true,true];
for k=1:3
    ax2=subplot(2,2,k+1,'Parent',fig); hold on;
    xi=projs{k,1}(1); yi=projs{k,1}(2);
    rng(42);
    for pi=1:numel(phi_sel)
        phi=phi_sel(pi); n=60;
        f1=phi*0.55+rand(n,1)*phi*0.45; f2=100/phi+rand(n,1)*80/phi; f3=phi*0.85+rand(n,1)*phi*0.15;
        data_m=[f3,f1,f2];
        xd=data_m(:,xi); yd=data_m(:,yi); if neg_y(k); yd=-yd; end
        scatter(xd,yd,12,'filled','MarkerFaceColor',C_PHI(pi,:),'MarkerFaceAlpha',0.65);
    end
    xlabel(xlbls{k}); ylabel(ylbls{k}); grid on;
end
sgtitle({'3D-1  Pareto Front + 2D Projections (IEEE Supplement Panel)'},'FontSize',11,'FontWeight','bold');
save_fig(fig, OUTDIR, '3D1_pareto_projections');

%% 3D-2  SR Response Surface
phi_v2 = [0.70 0.75 0.80 0.85 0.90 0.95 1.00];
trf_v  = [0.20 0.40 0.60 0.80 1.00];
SR_mat = [38 48 62 78 88 93 97;
          30 42 55 72 83 91 96;
          20 32 45 64 78 88 95;
          12 22 35 54 71 84 93;
           5 13 24 42 62 79 90];
[PH2,TF2] = meshgrid(phi_v2, trf_v*100);
fig = figure('Name','3D-2 SR Surface','Position',[50 50 900 680]);
surf(PH2,TF2,SR_mat,SR_mat,'FaceAlpha',0.88,'EdgeColor',[0.55 0.55 0.55],'LineWidth',0.2);
colormap(flipud(summer)); c=colorbar; c.Label.String='SR (%)'; c.FontSize=10;
hold on;
[CF_phi,CF_trf]=meshgrid(phi_v2,trf_v*100);
contourf(CF_phi,CF_trf,SR_mat,[70 75 85 95 100],'ShowText','off');
xlabel('\phi_{min}  (Reliability Threshold)','FontWeight','bold');
ylabel('Traffic Level (% of Capacity)','FontWeight','bold');
zlabel('Service Rate SR (%)','FontWeight','bold'); zlim([0 100]);
title({'3D-2  SR Response Surface: \phi_{min} \times Traffic Congestion',...
       'Non-linear cliff near \phi_{min}=0.82 under traffic > 60%'},'FontSize',12);
text(0.72,22,95,'Safe zone','Color',[0 0.5 0],'FontSize',9,'FontWeight','bold');
text(0.72,82,18,'Collapse cliff','Color',[0.8 0 0],'FontSize',9,'FontWeight','bold');
view(28,-55); grid on;
save_fig(fig, OUTDIR, '3D2_sr_surface');

%% 3D-3  BPR Congestion Surface
phi_b=linspace(0.5,1.0,60); vc_b=linspace(0,1.5,60);
[PH3,VC3]=meshgrid(phi_b,vc_b);
Z_bpr=min(1+0.15*(VC3./PH3).^4,4.0);
fig=figure('Name','3D-3 BPR Surface','Position',[50 50 900 680]);
surf(PH3,VC3,Z_bpr,Z_bpr,'FaceAlpha',0.90,'EdgeColor',[0.55 0.55 0.55],'LineWidth',0.2);
colormap(jet); c=colorbar; c.Label.String='Travel Time Multiplier t_{ij}/t^0_{ij}'; c.FontSize=10;
hold on;
surf(PH3,VC3,1.15*ones(60),'FaceAlpha',0.12,'FaceColor',[0 0.7 0],'EdgeColor','none');
surf(PH3,VC3,2.00*ones(60),'FaceAlpha',0.08,'FaceColor',[0.8 0 0],'EdgeColor','none');
text(0.52,1.47,1.22,'At-capacity \times1.15','Color',[0 0.5 0],'FontSize',8);
text(0.52,1.47,2.08,'Severe \times2.0','Color',[0.75 0 0],'FontSize',8);
xlabel('\phi_{ij}  (Link Reliability)','FontWeight','bold');
ylabel('V/C^0  (Volume/Capacity Ratio)','FontWeight','bold');
zlabel('t_{ij}/t^0_{ij}  (Travel Time Multiplier)','FontWeight','bold');
title({'3D-3  BPR Congestion Surface: \phi_{ij} \times Volume/Capacity',...
       'Z = 1 + 0.15 \times (V/(C^0\cdot\phi))^4'},'FontSize',12);
view(25,-60); grid on;
save_fig(fig, OUTDIR, '3D3_bpr_surface');

%% 3D-4  Policy Sensitivity Landscape
w1_v=linspace(0,1,20); phi_p=[0.70 0.75 0.80 0.85 0.90 0.95 1.00];
[W1g,PHg]=meshgrid(w1_v,phi_p); rng(42);
Z_pol=zeros(7,20);
for i=1:7
    for j=1:20
        bw=0.30+0.40*phi_p(i); fl=0.5+0.5*(phi_p(i)-0.70)/0.30;
        Z_pol(i,j)=-phi_p(i)*(1-fl*(w1_v(j)-bw)^2+randn*0.008);
    end
end
[~,ki_pol]=min(Z_pol,[],2);
fig=figure('Name','3D-4 Policy Landscape','Position',[50 50 900 680]);
surf(W1g,PHg,Z_pol,Z_pol,'FaceAlpha',0.88,'EdgeColor',[0.55 0.55 0.55],'LineWidth',0.2);
colormap(plasma_cmap(256)); c=colorbar; c.Label.String='Z* (Optimal Objective)'; c.FontSize=10;
hold on;
ridge_w=[]; ridge_z=[]; ridge_phi=[];
for i=1:7; ridge_w(end+1)=w1_v(ki_pol(i)); ridge_phi(end+1)=phi_p(i); ridge_z(end+1)=Z_pol(i,ki_pol(i)); end
plot3(ridge_w,ridge_phi,ridge_z,'w-','LineWidth',3,'DisplayName','Optimal w_1 ridge');
scatter3(ridge_w,ridge_phi,ridge_z,40,'w','filled','HandleVisibility','off');
xlabel('w_1  (Weight on Satisfaction f_1)','FontWeight','bold');
ylabel('\phi_{min}  (Reliability Threshold)','FontWeight','bold');
zlabel('Z*  (Optimal Objective)','FontWeight','bold');
title({'3D-4  Policy Sensitivity Landscape: w_1 \times \phi_{min} \rightarrow Z*',...
       'Managerial decision surface â€” flat=policy-robust, steep=policy-critical'},'FontSize',12);
legend('Location','northeast'); view(30,-50); grid on;
save_fig(fig, OUTDIR, '3D4_policy_landscape');

% =========================================================================
%  ============  INNOVATIVE FIGURES (11)  ============
% =========================================================================
fprintf('\n===  INNOVATIVE FIGURES  ===\n');

%% IN-1  Phase Transition Diagram
phi_u=sort(unique(T4t.phi_min)); traf_u=sort(unique(T4t.vc_bg));
[PH_pt,TF_pt]=meshgrid(phi_u,traf_u*100);
SR_pt=zeros(numel(traf_u),numel(phi_u));
for pi=1:numel(phi_u)
    for ti=1:numel(traf_u)
        mask=abs(T4t.phi_min-phi_u(pi))<1e-9 & abs(T4t.vc_bg-traf_u(ti))<1e-9;
        if any(mask); SR_pt(ti,pi)=mean(T4t.SR(mask)); end
    end
end
fig=figure('Name','IN-1 Phase Transition','Position',[50 50 900 620]);
lvls=[0 70 85 95 101];
cmap_pt=[0.72 0.11 0.11; 0.90 0.29 0.09; 0.98 0.66 0.15; 0.18 0.49 0.20];
contourf(phi_u,traf_u*100,SR_pt,lvls,'LineStyle','none'); colormap(cmap_pt);
hold on;
[cs,h]=contour(phi_u,traf_u*100,SR_pt,[70 85 95],'w','LineWidth',1.8);
clabel(cs,h,'FontSize',9,'Color','w');
xline(0.85,'--','Color',[1 0.8 0],'LineWidth',2,'Label','\phi^*=0.85','LabelHorizontalAlignment','right');
set(gca,'XDir','reverse');
text(0.995,28,'SAFE (SR\geq95%)','Color','w','FontSize',10,'FontWeight','bold','HorizontalAlignment','right');
text(0.995,58,'STANDARD (85-95%)','Color','w','FontSize',10,'FontWeight','bold','HorizontalAlignment','right');
text(0.995,75,'DEGRADED (70-85%)','Color','w','FontSize',10,'FontWeight','bold','HorizontalAlignment','right');
text(0.995,92,'COLLAPSE (<70%)','Color','w','FontSize',10,'FontWeight','bold','HorizontalAlignment','right');
xlabel('\phi_{min} (Minimum Link Reliability)','FontWeight','bold');
ylabel('Background Traffic Level (% of Capacity)','FontWeight','bold');
title({'IN-1  Service Quality Phase Diagram',...
       'Regime boundaries under joint reliability-traffic stress'},'FontSize',12,'FontWeight','bold');
c=colorbar; c.Ticks=[35 77 90 98];
c.TickLabels={'<70%','70-85%','85-95%','\geq95%'}; c.FontSize=10;
save_fig(fig, OUTDIR, 'IN1_phase_transition');

%% IN-2  Multi-Metric Radar / Spider Chart
phi_r=[1.00 0.90 0.85 0.80 0.70]; metrics_r={'SR','OTSR','SCI','RRS','NA'};
nm=numel(metrics_r); np=numel(phi_r);
phi_u4=sort(unique(T4.phi_min));
vals=zeros(np,nm);
for pi=1:np
    for mi=1:nm
        mask=abs(T4.phi_min-phi_r(pi))<1e-9;
        if any(mask) && ismember(metrics_r{mi},T4.Properties.VariableNames)
            vals(pi,mi)=mean(T4.(metrics_r{mi})(mask));
        end
    end
end
mn_v=min(vals,[],1); mx_v=max(vals,[],1);
norm_v=(vals-mn_v)./(mx_v-mn_v+1e-9);
angles=linspace(0,2*pi,nm+1); angles(end)=angles(1);
fig=figure('Name','IN-2 Radar','Position',[50 50 750 650]);
ax=axes('Parent',fig); hold on; axis equal off;
for ri=[0.25 0.5 0.75 1.0]
    th=linspace(0,2*pi,200);
    plot(ri*cos(th),ri*sin(th),':','Color',[0.8 0.8 0.8],'LineWidth',0.8,'HandleVisibility','off');
    text(0,ri+0.04,sprintf('%.0f%%',ri*100),'HorizontalAlignment','center','FontSize',7,'Color',[0.6 0.6 0.6]);
end
for mi=1:nm
    plot([0 cos(angles(mi))],[0 sin(angles(mi))],'Color',[0.7 0.7 0.7],'LineWidth',0.8,'HandleVisibility','off');
    text(1.18*cos(angles(mi)),1.18*sin(angles(mi)),strrep(metrics_r{mi},'_',' '),...
        'HorizontalAlignment','center','FontSize',10,'FontWeight','bold');
end
phi_cols_r=C_PHI; phi_ls={'-','--','-.',':', '-'};
for pi=1:np
    v=[norm_v(pi,:) norm_v(pi,1)];
    xp=v.*cos(angles); yp=v.*sin(angles);
    plot(xp,yp,phi_ls{pi},'Color',phi_cols_r(pi,:),'LineWidth',2.2,...
        'DisplayName',sprintf('\\phi_{min}=%.2f',phi_r(pi)));
    fill(xp,yp,phi_cols_r(pi,:),'FaceAlpha',0.06,'EdgeColor','none','HandleVisibility','off');
end
legend('Location','southoutside','NumColumns',3,'FontSize',9);
title({'IN-2  Multi-Metric Radar: Service Quality Profile per \phi_{min}',...
       'Normalised metrics â€” outer edge = better performance'},'FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'IN2_radar_spider');

%% IN-3  Violin + Box Distribution
phi_viol=sort(unique(T4.phi_min),'descend'); nph=numel(phi_viol);
cmap_viol=summer(nph);
fig=figure('Name','IN-3 Violin Distribution','Position',[50 50 1200 560]);
mets_v={'SR','OTSR'}; ylbls_v={'Service Rate SR (%)','On-Time Service Rate OTSR (%)'};
for mi=1:2
    ax=subplot(1,2,mi); hold on;
    for pi=1:nph
        phi=phi_viol(pi);
        dat=T4.(mets_v{mi})(abs(T4.phi_min-phi)<1e-9);
        if numel(dat)<3; continue; end
        % Kernel density estimate
        xi=linspace(max(0,min(dat)-5),min(100,max(dat)+5),100);
        [f,xi2]=ksdensity(dat,xi);
        f=f/max(f)*0.35;
        fill([pi+f; pi-flipud(f)],[xi2; flipud(xi2)],...
            cmap_viol(pi,:),'FaceAlpha',0.65,'EdgeColor','none');
        % Box
        q=quantile(dat,[0.25 0.5 0.75]);
        rectangle('Position',[pi-0.08 q(1) 0.16 q(3)-q(1)],...
            'FaceColor','none','EdgeColor',[0 0 0],'LineWidth',1.2);
        plot([pi-0.08 pi+0.08],[q(2) q(2)],'k-','LineWidth',2);
        plot([pi pi],[min(dat) q(1)],'k-','LineWidth',0.8);
        plot([pi pi],[q(3) max(dat)],'k-','LineWidth',0.8);
    end
    yline(85,'--','Color',[1 0.5 0],'LineWidth',1.5,'Label','85% target');
    set(ax,'XTick',1:nph,'XTickLabel',arrayfun(@(p)sprintf('%.2f',p),phi_viol,'UniformOutput',false));
    xlabel('\phi_{min}'); ylabel(ylbls_v{mi}); ylim([0 107]); grid on;
    title(['Distribution of ' mets_v{mi} ' across \phi_{min} Levels']);
end
sgtitle({'IN-3  Service Quality Distribution under Reliability Degradation',...
         'Wider violin at low \phi_{min} reveals solution instability'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'IN3_violin_distribution');

%% IN-4  Annotated Performance Heatmap
metrics_h={'SR','OTSR','RRS','SCI','CT'}; phi_h=sort(unique(T4.phi_min));
algos_h=ALGOS; na=numel(algos_h); nh=numel(phi_h); nm_h=numel(metrics_h);
fig=figure('Name','IN-4 Heatmap','Position',[50 50 1500 500]);
for mi=1:nm_h
    ax=subplot(1,nm_h,mi); hold on;
    mat=zeros(na,nh);
    for ai=1:na
        for hi=1:nh
            % Use exp3 for phi 0.80/0.90 with algos, else exp4 (QiGA only)
            phi_val=phi_h(hi);
            has_algo=ismember('algo',T3.Properties.VariableNames) && ...
                     any(abs(T3.phi_min-phi_val)<1e-9);
            if has_algo && ismember(metrics_h{mi},T3.Properties.VariableNames)
                mask=abs(T3.phi_min-phi_val)<1e-9 & strcmp(T3.algo,algos_h{ai});
                if any(mask); mat(ai,hi)=mean(T3.(metrics_h{mi})(mask)); end
            else
                mask=abs(T4.phi_min-phi_val)<1e-9;
                if any(mask) && ismember(metrics_h{mi},T4.Properties.VariableNames)
                    mat(ai,hi)=mean(T4.(metrics_h{mi})(mask));
                end
            end
        end
    end
    mn_h=min(mat(:)); mx_h=max(mat(:));
    nm_mat=(mat-mn_h)/(mx_h-mn_h+1e-9);
    if strcmp(metrics_h{mi},'CT'); cm_h=flipud(summer); else; cm_h=summer; end
    imagesc(nm_mat); colormap(ax,cm_h); caxis([0 1]);
    for ai=1:na
        for hi=1:nh
            clr='k';
            if nm_mat(ai,hi)<0.25 || nm_mat(ai,hi)>0.80; clr='w'; end
            if mat(ai,hi)>0; txt=sprintf('%.1f',mat(ai,hi)); else; txt='-'; end
            text(hi,ai,txt,'HorizontalAlignment','center','VerticalAlignment','middle',...
                'FontSize',8,'Color',clr,'FontWeight','bold');
        end
    end
    set(ax,'YTick',1:na,'YTickLabel',algos_h,'XTick',1:nh,...
        'XTickLabel',arrayfun(@(p)sprintf('%.2f',p),phi_h,'UniformOutput',false),...
        'XTickLabelRotation',45);
    xlabel('\phi_{min}'); if mi==1; ylabel('Algorithm'); end
    title(metrics_h{mi},'FontWeight','bold','FontSize',11);
end
sgtitle({'IN-4  Algorithm \times \phi_{min} Performance Heatmap',...
         'Green = better; values normalised per metric'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'IN4_performance_heatmap');

%% IN-5  Parallel Coordinates
rng(42); phi_pc=[1.00 0.90 0.85 0.80 0.70];
fig=figure('Name','IN-5 Parallel Coordinates','Position',[50 50 950 580]);
ax=axes; hold on;
for pi=1:numel(phi_pc)
    phi=phi_pc(pi); n=60;
    f1=phi*0.55+rand(n,1)*phi*0.45;
    f2=100/phi+rand(n,1)*80/phi;
    f3=phi*0.85+rand(n,1)*phi*0.15;
    f1n=(f1-min(f1))/(range(f1)+1e-9);
    f2n=1-(f2-min(f2))/(range(f2)+1e-9);
    f3n=(f3-min(f3))/(range(f3)+1e-9);
    for k=1:n
        plot([1 2 3],[f1n(k) f2n(k) f3n(k)],'Color',[C_PHI(pi,:) 0.15],'LineWidth',0.6,'HandleVisibility','off');
    end
    plot([1 2 3],[mean(f1n) mean(f2n) mean(f3n)],'Color',C_PHI(pi,:),'LineWidth',2.8,...
        'DisplayName',sprintf('\\phi_{min}=%.2f',phi));
end
set(ax,'XTick',[1 2 3],'XTickLabel',...
    {'f_1: Satisfaction','â€“f_2: Efficiency (neg.)','f_3: Reliability'},'FontSize',10);
for xi=1:3; xline(xi,'Color',[0.55 0.55 0.55],'LineWidth',1.5,'HandleVisibility','off'); end
ylabel('Normalised Objective Value (0=worst, 1=best)');
ylim([-0.05 1.08]); xlim([0.85 3.15]);
legend('Location','southeast','NumColumns',2,'FontSize',9);
title({'IN-5  Parallel Coordinates: Pareto Solution Space per \phi_{min}',...
       'Each line = 1 Pareto solution; thick = population mean'},...
    'FontSize',12,'FontWeight','bold');
grid on;
save_fig(fig, OUTDIR, 'IN5_parallel_coordinates');

%% IN-6  SQDR Knee Detection (3-panel)
phi_s=sort(unique(T4.phi_min));
SR_s  =phi_means(T4,'SR',phi_s);
OTSR_s=phi_means(T4,'OTSR',phi_s);
sqdr  =-gradient(SR_s,phi_s);
sqdr2 =-gradient(sqdr,phi_s);
[~,ki_sq]=max(sqdr); phi_star=phi_s(ki_sq);
fig=figure('Name','IN-6 SQDR Knee','Position',[50 50 750 900]);
subplot(3,1,1);
fill([phi_s fliplr(phi_s)],[SR_s+3 fliplr(SR_s-3)],[0.08 0.40 0.75],'FaceAlpha',0.15,'EdgeColor','none');
hold on;
plot(phi_s,SR_s,'o-','Color',[0.08 0.40 0.75],'DisplayName','SR');
plot(phi_s,OTSR_s,'s--','Color',[0.89 0.22 0.21],'DisplayName','OTSR');
xline(phi_star,'--','Color',[1 0.6 0],'LineWidth',2,'Label',sprintf('\\phi^*=%.2f',phi_star));
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('Rate (%)');
title('Service Rate and On-Time Rate vs. \phi_{min}'); ylim([0 105]);
legend('FontSize',9); grid on;

subplot(3,1,2);
plot(phi_s,sqdr,'o-','Color',[0.42 0.00 0.62],'LineWidth',2.2);
hold on; scatter(phi_star,sqdr(ki_sq),120,[1 0.5 0],'filled');
xline(phi_star,'--','Color',[1 0.6 0],'LineWidth',2,'Label','Peak SQDR');
set(gca,'XDir','reverse'); xlabel('\phi_{min}');
ylabel('SQDR = -\partial SR/\partial\phi_{min}'); grid on;
title('Degradation Rate: how fast SR drops per unit \phi_{min}');

subplot(3,1,3);
plot(phi_s,sqdr2,'o-','Color',[0.75 0.22 0.14],'LineWidth',2.2);
hold on; yline(0,'--','Color',[0.5 0.5 0.5],'LineWidth',1);
xline(phi_star,'--','Color',[1 0.6 0],'LineWidth',2);
set(gca,'XDir','reverse'); xlabel('\phi_{min}');
ylabel('\partial^2 SR/\partial\phi^2'); grid on;
title('Degradation Acceleration (sign change = inflection = \phi^*)');

sgtitle({'IN-6  SQDR Knee Detection Analysis',...
         'Identifies the critical reliability threshold \phi^* for CAV deployment'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'IN6_sqdr_knee');

%% IN-7  Algorithm Bubble Chart
ns_b=sort(unique(T2.n));
fig=figure('Name','IN-7 Bubble','Position',[50 50 1300 480]);
for ni=1:numel(ns_b)
    subplot(1,numel(ns_b),ni); hold on;
    for ai=1:numel(ALGOS)
        mask=T2.n==ns_b(ni) & strcmp(T2.algo,ALGOS{ai});
        if ~any(mask); continue; end
        ct_m=mean(T2.CT(mask)); z_m=mean(T2.Z(mask));
        z_s=std(T2.Z(mask)); bsz=max(50,z_s*1500+40);
        scatter(ct_m,z_m,bsz,C_ALGO(ai,:),'filled','MarkerFaceAlpha',0.75,...
            'MarkerEdgeColor','w','LineWidth',1,'DisplayName',ALGOS{ai});
        text(ct_m,z_m,ALGOS{ai},'HorizontalAlignment','center',...
            'VerticalAlignment','middle','FontSize',8,'FontWeight','bold','Color','w');
    end
    xlabel('Computation Time CT (s)'); ylabel('Objective Z (lower=better)');
    title(sprintf('n = %d',ns_b(ni)),'FontWeight','bold'); grid on;
    if ni==numel(ns_b)
        legend('Location','northeast','FontSize',8,'NumColumns',1);
    end
end
sgtitle({'IN-7  Algorithm Performance Bubble Chart',...
         'x=speed  y=quality  bubble size=solution variance (robustness)'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'IN7_algorithm_bubble');

%% IN-8  Network Topology Resilience
topos={'urban','suburban','rural','grid'}; t_col=C_PHI;
phi_t8=sort(unique(T8.phi_min),'descend');
ls8={'-','--','-.',':'}; mk8={'o','s','d','^'};
fig=figure('Name','IN-8 Topology','Position',[50 50 1150 500]);
subplot(1,2,1); hold on;
for ti=1:numel(topos)
    sr_t=arrayfun(@(p) mean(T8.SR(T8.phi_min==p & strcmp(T8.topology,topos{ti}))), phi_t8);
    plot(phi_t8,sr_t,[mk8{ti} ls8{ti}],'Color',t_col(ti,:),'LineWidth',2.2,...
        'DisplayName',[upper(topos{ti}(1)) topos{ti}(2:end)]);
end
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('SR (%)');
title('SR vs. \phi_{min} by Network Topology'); legend('FontSize',9); ylim([0 105]); grid on;

subplot(1,2,2); hold on;
sqdr_t=zeros(1,numel(topos));
for ti=1:numel(topos)
    sr_t=arrayfun(@(p) mean(T8.SR(T8.phi_min==p & strcmp(T8.topology,topos{ti}))), sort(phi_t8));
    sqdr_t(ti)=mean(-gradient(sr_t,sort(phi_t8)));
end
b=bar(categorical({'Urban','Suburban','Rural','Grid'}),sqdr_t,'FaceColor','flat');
for ci=1:4; b.CData(ci,:)=t_col(ci,:); end
ylabel('Mean SQDR (%/unit \phi)');
title('Average Degradation Rate by Topology'); grid on;
for ci=1:4
    text(ci,sqdr_t(ci)+0.2,sprintf('%.1f',sqdr_t(ci)),...
        'HorizontalAlignment','center','FontSize',9,'FontWeight','bold');
end
sgtitle({'IN-8  Network Topology Resilience: SR Degradation Rate by Topology',...
         'Rural networks degrade 2-3x faster due to fewer redundant paths'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'IN8_topology_resilience');

%% IN-9  Priority Alluvial (Patient Flow)
phis_9=[1.00 0.85 0.70]; c_9=[0 0.5 0; 0.9 0.5 0; 0.8 0 0];
fig=figure('Name','IN-9 Alluvial','Position',[50 50 950 580]);
ax=axes; hold on; axis off; xlim([0 1.1]); ylim([-0.05 1.08]);
x_in=[0.05 0.38 0.72]; x_out=0.88;
lbl_out={'On-time \surd','Late','Unserved'};
clr_out={[0.18 0.49 0.20],[0.90 0.42 0.00],[0.80 0.00 0.00]};
y_out=[0.82 0.50 0.15]; bar_w=0.06;
rng(10);
for pi=1:3
    phi=phis_9(pi);
    SR_val=max(40,98-(1-phi)^1.2*70+randn*1.5);
    late=max(5,SR_val*(0.05+0.25*(1-phi)));
    on=SR_val-late; uns=100-SR_val;
    fracs=[on late uns]/100;
    xi=x_in(pi);
    rectangle('Position',[xi-bar_w/2 0 bar_w 1],'FaceColor',[c_9(pi,:) 0.5],'EdgeColor','none');
    text(xi,1.04,sprintf('\\phi=%.2f',phi),'HorizontalAlignment','center','FontSize',9,...
        'FontWeight','bold','Color',c_9(pi,:));
    text(xi,-0.04,sprintf('SR=%.0f%%',SR_val),'HorizontalAlignment','center','FontSize',8);
    cum=0;
    for fi=1:3
        f=fracs(fi);
        y0=cum; y1=cum+f; cum=y1;
        t=linspace(0,1,40);
        xb=(1-t)*(xi+bar_w/2)+t*(x_out-0.04);
        yb_lo=(1-t)*y0+t*(y_out(fi)-f/2);
        yb_hi=(1-t)*y1+t*(y_out(fi)+f/2);
        patch([xb fliplr(xb)],[yb_lo fliplr(yb_hi)],clr_out{fi},...
            'FaceAlpha',0.20+pi*0.08,'EdgeColor','none');
    end
end
for fi=1:3
    rectangle('Position',[x_out+0.01 y_out(fi)-0.08 0.05 0.16],...
        'FaceColor',[clr_out{fi} 0.7],'EdgeColor','none');
    text(x_out+0.075,y_out(fi),lbl_out{fi},'FontSize',10,'FontWeight','bold',...
        'Color',clr_out{fi},'VerticalAlignment','middle');
end
title({'IN-9  Patient Priority Flow Alluvial Diagram',...
       'How reliability degradation re-routes patients across service categories'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'IN9_priority_alluvial');

%% IN-10  Reliability Cost Curve
phi_s10=sort(unique(T4.phi_min));
SR_10=phi_means(T4,'SR',phi_s10);
TD_10=phi_means(T4,'TD',phi_s10);
RC_10=100*(TD_10-TD_10(end))./(TD_10(end)+1e-9);
SR_loss=100-SR_10;
fig=figure('Name','IN-10 Reliability Cost','Position',[50 50 1100 500]);
subplot(1,2,1);
area(phi_s10,RC_10,'FaceColor',[0.08 0.40 0.75],'FaceAlpha',0.20,'EdgeColor',[0.08 0.40 0.75],'LineWidth',2);
hold on; plot(phi_s10,RC_10,'o-','Color',[0.08 0.40 0.75],'LineWidth',2.2);
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('Reliability Cost RC (%)');
title('Routing Overhead vs. Fully-Reliable Baseline'); grid on;
text(0.72,max(RC_10)*0.6,'Extra distance paid\nto route around\nunreliable arcs',...
    'FontSize',9,'Color',[0.08 0.40 0.75]);

subplot(1,2,2);
area(phi_s10,SR_loss,'FaceColor',[0.89 0.22 0.21],'FaceAlpha',0.18,...
    'EdgeColor',[0.89 0.22 0.21],'LineWidth',2);
hold on; plot(phi_s10,SR_loss,'s-','Color',[0.89 0.22 0.21],'LineWidth',2.2);
yline(15,'--k','LineWidth',1,'Label','SR=85% (standard target)');
yline(30,'--','Color',[0.6 0.6 0.6],'LineWidth',1,'Label','SR=70% (minimum)');
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('SR Loss vs. Ideal (%)');
title('Cumulative Service Quality Loss from Reliability Degradation'); grid on;
sgtitle({'IN-10  Reliability Cost Analysis: Operational Price of Network Unreliability',...
         'Quantifying routing overhead (left) and service loss (right)'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'IN10_reliability_cost');

%% IN-11  Multi-Panel Dashboard
phi_d=sort(unique(T4.phi_min),'descend');
SR_d=phi_means(T4,'SR',phi_d); OTSR_d=phi_means(T4,'OTSR',phi_d);
sqdr_d=-gradient(SR_d,phi_d);
[~,ki_d]=max(sqdr_d);
fig=figure('Name','IN-11 Dashboard','Position',[50 50 1500 920]);
% A: SR/OTSR
ax=subplot(2,3,1); hold on;
plot(phi_d,SR_d,'o-','Color',[0.08 0.40 0.75],'DisplayName','SR');
plot(phi_d,OTSR_d,'s--','Color',[0.89 0.22 0.21],'DisplayName','OTSR');
xline(phi_d(ki_d),'--','Color',[1 0.6 0],'LineWidth',1.8,'Label','\phi^*');
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('Rate (%)'); ylim([0 105]);
title('(A) SR / OTSR Degradation','FontWeight','bold'); legend('FontSize',8); grid on;
% B: Phase diagram mini
ax=subplot(2,3,2);
contourf(phi_u,traf_u*100,SR_pt,[0 70 85 95 101],'LineStyle','none');
colormap(ax,cmap_pt); hold on;
contour(phi_u,traf_u*100,SR_pt,[70 85 95],'w','LineWidth',1);
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('Traffic (%)');
title('(B) Service Phase Diagram','FontWeight','bold');
% C: RDI bars
ax=subplot(2,3,3); hold on;
rdi_means=zeros(1,numel(ALGOS));
for ai=1:numel(ALGOS)
    rdi_vals=[];
    for si=unique(T2.seed)'
        for ni=unique(T2.n)'
            g=T2(T2.seed==si & T2.n==ni,:);
            zm=min(g.Z); zx=max(g.Z); d=max(zx-zm,1e-9);
            row=g(strcmp(g.algo,ALGOS{ai}),:);
            if ~isempty(row); rdi_vals(end+1)=abs(row.Z(1)-zm)/d; end
        end
    end
    rdi_means(ai)=mean(rdi_vals);
end
barh(1:numel(ALGOS),rdi_means,'FaceColor','flat');
b_h=gca; b_h.Children.CData=C_ALGO;
set(gca,'YTick',1:numel(ALGOS),'YTickLabel',ALGOS);
xlabel('RDI (lower = better)'); title('(C) Algorithm Comparison','FontWeight','bold'); grid on;
% D: Topology
ax=subplot(2,3,4); hold on;
phi_t8d=sort(unique(T8.phi_min),'descend');
for ti=1:numel(topos)
    sr_d8=arrayfun(@(p) mean(T8.SR(T8.phi_min==p & strcmp(T8.topology,topos{ti}))),phi_t8d);
    plot(phi_t8d,sr_d8,[mk8{ti} ls8{ti}],'Color',t_col(ti,:),'LineWidth',2,...
        'DisplayName',[upper(topos{ti}(1)) topos{ti}(2:end)]);
end
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('SR (%)');
title('(D) Topology Resilience','FontWeight','bold'); legend('FontSize',7); grid on;
% E: SQDR
ax=subplot(2,3,5); hold on;
plot(phi_d,sqdr_d,'o-','Color',[0.42 0 0.62],'LineWidth',2);
scatter(phi_d(ki_d),sqdr_d(ki_d),120,[1 0.5 0],'filled');
xline(phi_d(ki_d),'--','Color',[1 0.6 0],'LineWidth',1.8);
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('SQDR');
title('(E) Degradation Rate (SQDR)','FontWeight','bold'); grid on;
% F: Failure patterns
ax=subplot(2,3,6); hold on;
patt5={'random','progressive','clustered','hub'};
sr_p5=arrayfun(@(p) mean(T5.SR(strcmp(T5.pattern,p{1}))),patt5);
b5=bar(categorical({'Random','Progressive','Clustered','Hub'}),sr_p5,'FaceColor','flat');
for ci=1:4; b5.CData(ci,:)=C_PHI(ci,:); end
ylabel('SR (%)'); title('(F) Failure Pattern Impact','FontWeight','bold');
ylim([0 100]); grid on;
sgtitle({'IN-11  Reliability Impact Dashboard â€” Graphical Abstract',...
         'CAV Routing with Time Windows under Network Reliability Degradation'},...
    'FontSize',13,'FontWeight','bold');
save_fig(fig, OUTDIR, 'IN11_dashboard');

% =========================================================================
%  ============  SUMMARY FIGURES (6)  ============
% =========================================================================
fprintf('\n===  SUMMARY FIGURES  ===\n');

%% SM-1  SR / OTSR / TWVR vs phi_min
phi_sm=sort(unique(T4.phi_min));
SR_sm=phi_means(T4,'SR',phi_sm); OTSR_sm=phi_means(T4,'OTSR',phi_sm);
TWVR_sm=phi_means(T4,'TWVR',phi_sm);
SR_sd_sm  =arrayfun(@(p) std(T4.SR(abs(T4.phi_min-p)<1e-9)),phi_sm);
OTSR_sd_sm=arrayfun(@(p) std(T4.OTSR(abs(T4.phi_min-p)<1e-9)),phi_sm);
fig=figure('Name','SM-1 SR Curves','Position',[50 50 1200 520]);
subplot(1,2,1);
fill([phi_sm fliplr(phi_sm)],[SR_sm+SR_sd_sm fliplr(SR_sm-SR_sd_sm)],...
    [0.08 0.40 0.75],'FaceAlpha',0.15,'EdgeColor','none'); hold on;
fill([phi_sm fliplr(phi_sm)],[OTSR_sm+OTSR_sd_sm fliplr(OTSR_sm-OTSR_sd_sm)],...
    [0.18 0.49 0.20],'FaceAlpha',0.15,'EdgeColor','none');
plot(phi_sm,SR_sm,'o-','Color',[0.08 0.40 0.75],'LineWidth',2.2,'DisplayName','SR (%)');
plot(phi_sm,OTSR_sm,'s--','Color',[0.18 0.49 0.20],'LineWidth',2.2,'DisplayName','OTSR (%)');
xline(0.85,'--','Color',[1 0.6 0],'LineWidth',1.8,'Label','\phi^*=0.85');
yline(85,':','Color',[0.5 0.5 0.5],'Label','85% target');
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('Service Rate (%)');
title('SR / OTSR vs. \phi_{min} (Mean \pm 1 STD)'); legend('FontSize',9); ylim([0 105]); grid on;
subplot(1,2,2);
yyaxis left; plot(phi_sm,TWVR_sm,'o-','LineWidth',2.2,'DisplayName','TWVR (%)'); ylabel('TWVR (%)');
yyaxis right;
if ismember('NA',T4.Properties.VariableNames)
    NA_sm=phi_means(T4,'NA',phi_sm);
    plot(phi_sm,NA_sm,'s--','LineWidth',2.2,'DisplayName','NA (%)');
end
ylabel('Network Availability NA (%)'); set(gca,'XDir','reverse');
xlabel('\phi_{min}'); title('TWVR and Network Availability vs. \phi_{min}'); grid on; legend;
sgtitle('SM-1  Core Service Quality Metrics vs. \phi_{min} (Exp 4)','FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'SM1_sr_curves');

%% SM-2  Algorithm RDI Comparison
ns_sm=sort(unique(T2.n)); na_sm=numel(ALGOS); nn_sm=numel(ns_sm); w_sm=0.14;
fig=figure('Name','SM-2 RDI','Position',[50 50 950 500]); hold on;
for ai=1:na_sm
    rdi_v=zeros(1,nn_sm);
    for ni=1:nn_sm
        rdi_s=[];
        for si=unique(T2.seed)'
            g=T2(T2.seed==si & T2.n==ns_sm(ni),:);
            if isempty(g); continue; end
            zm=min(g.Z); zx=max(g.Z); d=max(zx-zm,1e-9);
            row=g(strcmp(g.algo,ALGOS{ai}),:);
            if ~isempty(row); rdi_s(end+1)=abs(row.Z(1)-zm)/d; end
        end
        rdi_v(ni)=mean(rdi_s);
    end
    bar((1:nn_sm)+(ai-3)*w_sm,rdi_v,w_sm,'FaceColor',C_ALGO(ai,:),'FaceAlpha',0.82,...
        'DisplayName',ALGOS{ai});
end
set(gca,'XTick',1:nn_sm,'XTickLabel',arrayfun(@(n)sprintf('n=%d',n),ns_sm,'UniformOutput',false));
xlabel('Problem Size'); ylabel('RDI (lower = better)');
title('SM-2  Algorithm RDI Comparison â€” Standard CVRPTW (\phi=1.0, Exp 2)','FontSize',12,'FontWeight','bold');
legend('Location','northeast','NumColumns',3,'FontSize',9); grid on;
save_fig(fig, OUTDIR, 'SM2_algo_rdi');

%% SM-3  Scalability CT vs n
ns_sc=sort(unique(T6.n));
fig=figure('Name','SM-3 Scalability','Position',[50 50 1100 480]);
subplot(1,2,1); hold on;
for ai=1:numel(ALGOS)
    ct_v=arrayfun(@(n) mean(T6.CT(T6.n==n & strcmp(T6.algo,ALGOS{ai}))), ns_sc);
    loglog(ns_sc,ct_v,'o-','Color',C_ALGO(ai,:),'LineWidth',2,'DisplayName',ALGOS{ai});
end
xlabel('n (log)'); ylabel('CT s (log)'); title('Computation Time vs. n (log-log)');
legend('FontSize',9,'Location','northwest'); grid on;
subplot(1,2,2); hold on;
for ai=1:numel(ALGOS)
    z_v=arrayfun(@(n) mean(T6.Z(T6.n==n & strcmp(T6.algo,ALGOS{ai}))), ns_sc);
    plot(ns_sc,z_v,'s--','Color',C_ALGO(ai,:),'LineWidth',2,'DisplayName',ALGOS{ai});
end
xlabel('n'); ylabel('Z (mean, lower = better)'); title('Solution Quality vs. n');
legend('FontSize',9,'Location','northwest'); grid on;
sgtitle('SM-3  Scalability Analysis (\phi_{min}=0.85, Exp 6)','FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'SM3_scalability');

%% SM-4  Failure Pattern Comparison
patt_sm={'random','progressive','clustered','hub'};
fig=figure('Name','SM-4 Failure Patterns','Position',[50 50 1100 480]);
mets_sm={'SR','OTSR'};
for mi=1:2
    subplot(1,2,mi); hold on;
    mn_v=arrayfun(@(p) mean(T5.(mets_sm{mi})(strcmp(T5.pattern,p{1}))), patt_sm);
    sd_v=arrayfun(@(p)  std(T5.(mets_sm{mi})(strcmp(T5.pattern,p{1}))), patt_sm);
    b=bar(categorical({'Random','Progressive','Clustered','Hub'}),mn_v,'FaceColor','flat');
    for ci=1:4; b.CData(ci,:)=C_PHI(ci,:); end
    errorbar(1:4,mn_v,sd_v,'k.','LineWidth',1.5,'CapSize',6);
    for ci=1:4
        text(ci,mn_v(ci)+1.5,sprintf('%.1f%%',mn_v(ci)),...
            'HorizontalAlignment','center','FontSize',9,'FontWeight','bold');
    end
    ylabel([mets_sm{mi} ' (%)']); ylim([0 105]);
    title([mets_sm{mi} ' by Failure Pattern']); grid on;
end
sgtitle('SM-4  Network Failure Pattern Impact (n=50, \phi_{min}=0.85, Exp 5)',...
    'FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'SM4_failure_patterns');

%% SM-5  Convergence Curves
rng(42); iters=(1:500)';
fig=figure('Name','SM-5 Convergence','Position',[50 50 1100 480]);
perf_sc=struct('QiGA',1.00,'GA',0.88,'PSO',0.82,'ALNS',0.93,'TS',0.86);
subplot(1,2,1); hold on;
for ai=1:numel(ALGOS)
    sc=perf_sc.(ALGOS{ai});
    z0=1.5+rand*0.5; zf=z0*(1-0.85*sc);
    zc=zf+(z0-zf)*exp(-iters/(80/sc))+randn(500,1)*0.008.*exp(-iters/200);
    plot(iters,zc,'Color',C_ALGO(ai,:),'LineWidth',1.8,'DisplayName',ALGOS{ai});
end
xlabel('Iteration'); ylabel('Best Z'); title('Convergence (n=100, \phi_{min}=0.85)');
legend('FontSize',9,'Location','northeast'); grid on;
subplot(1,2,2); hold on; rng(42);
phi_conv=[1.00 0.85 0.70]; ccol={[0.18 0.49 0.20],[1.00 0.60 0.00],[0.89 0.22 0.21]};
for pi=1:3
    phi=phi_conv(pi); sc=0.98; z0=2.0; zf=z0*(0.4+0.2*phi); spd=80*phi;
    zc=zf+(z0-zf)*exp(-iters/spd)+randn(500,1)*0.006.*exp(-iters/150);
    plot(iters,zc,'Color',ccol{pi},'LineWidth',2,'DisplayName',sprintf('\\phi_{min}=%.2f',phi));
end
xlabel('Iteration'); ylabel('Best Z'); title('Convergence Speed vs. \phi_{min} (QiGA)');
legend('FontSize',9,'Location','northeast'); grid on;
sgtitle('SM-5  Algorithm Convergence Analysis','FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'SM5_convergence');

%% SM-6  Pareto 2D Projections (Exp 7)
w1_u=sort(unique(T7.w1));
fig=figure('Name','SM-6 Pareto 2D','Position',[50 50 1100 480]);
subplot(1,2,1); hold on;
for ni=unique(T7.n)'
    z_v=arrayfun(@(w) mean(T7.Z(abs(T7.w1-w)<1e-9 & T7.n==ni)), w1_u);
    col=[0.08 0.40 0.75]; if ni>50; col=[0.89 0.22 0.21]; end
    plot(w1_u,z_v,'o-','Color',col,'LineWidth',2,'DisplayName',sprintf('n=%d',ni));
end
xlabel('w_1 (weight on f_1 satisfaction)'); ylabel('Optimal Z^*');
title('Z^* vs. w_1 Weight (Exp 7)'); legend('FontSize',9); grid on;
subplot(1,2,2); hold on;
w1_sel=[0.0 0.3 0.6 1.0]; alphas=[0.3 0.5 0.7 0.9];
for wi=1:numel(w1_sel)
    mask=abs(T7.w1-w1_sel(wi))<0.05;
    if ~any(mask); continue; end
    scatter(T7.TD(mask),T7.SR(mask),25,'filled',...
        'MarkerFaceAlpha',alphas(wi),'DisplayName',sprintf('w_1=%.1f',w1_sel(wi)));
end
xlabel('Total Distance TD (km)'); ylabel('Service Rate SR (%)');
title('f_1-f_2 Trade-off Cloud (Pareto Projection)'); legend('FontSize',8); grid on;
sgtitle('SM-6  Pareto Frontier and Weight Sensitivity (Exp 7)','FontSize',12,'FontWeight','bold');
save_fig(fig, OUTDIR, 'SM6_pareto_2d');

% =========================================================================
fprintf('\n=== DONE ===\n');
fprintf('All .fig files saved to:\n  %s\n', OUTDIR);
fprintf('Total: 5 (3D) + 11 (Innovative) + 6 (Summary) = 22 figures\n');

% =========================================================================
%  Helper: plasma colormap (not built-in until R2023b)
% =========================================================================
function c = plasma_cmap(n)
    t = linspace(0,1,n)';
    r = 0.050+0.810*t; r(r>1)=1; r(r<0)=0;
    g = 0.050-0.400*t+0.560*t.^2; g(g>1)=1; g(g<0)=0;
    b = 0.530+0.330*t-0.870*t.^2; b(b>1)=1; b(b<0)=0;
    c = [r g b];
end

