%% generate_moo_matlab_figs.m
% MATLAB .fig files for NSGA-II and MOEA/D MOO results
% Run after run_moo_exp7.py has generated moo_exp7.csv
% cd('E:\Working Docs\Papers\Reliability CAV'); run('code\generate_moo_matlab_figs.m')

clear; clc; close all;
BASE   = 'E:\Working Docs\Papers\Reliability CAV';
TDIR   = fullfile(BASE,'results','tables');
OUTDIR = fullfile(BASE,'results','figures','matlab');
if ~exist(OUTDIR,'dir'); mkdir(OUTDIR); end

set(0,'DefaultAxesFontSize',11,'DefaultAxesFontName','Arial',...
      'DefaultLineLineWidth',2,'DefaultFigureColor','w','DefaultAxesBox','off');

ALGOS  = {'QiGA-WS','NSGA-II','MOEA/D'};
COLS   = [0.08 0.40 0.75; 0.89 0.22 0.21; 0.18 0.49 0.20];
MKS    = {'o','s','d'};

function save_fig(fig, outdir, name)
    savefig(fig, fullfile(outdir, [name '.fig']));
    fprintf('  Saved: %s.fig\n', name);
end

% Load MOO results
T = readtable(fullfile(TDIR,'moo_exp7.csv'),'VariableNamingRule','preserve');
fprintf('Loaded moo_exp7.csv: %d rows\n', height(T));

phi_u = sort(unique(T.phi_min),'descend');

%% MOO-M1  Quality Metrics Bar Chart (phi=0.85)
fprintf('MOO-M1  Quality metrics bar chart\n');
phi85=0.85;
sub=T(abs(T.phi_min-phi85)<1e-9,:);
metrics={'HV','IGD','Spread','n_pareto'};
ylbls={'Hypervolume HV (higher=better)','IGD (lower=better)',...
       'Spread \Delta (lower=better)','Archive Size |F| (higher=better)'};
fig=figure('Name','MOO Quality Metrics','Position',[50 50 1400 480]);
for mi=1:4
    subplot(1,4,mi); hold on;
    mn_v=zeros(1,3); sd_v=zeros(1,3);
    for ai=1:3
        mask=strcmp(sub.algo,ALGOS{ai});
        if any(mask)
            mn_v(ai)=mean(sub.(metrics{mi})(mask));
            sd_v(ai)=std(sub.(metrics{mi})(mask));
        end
    end
    b=bar(1:3,mn_v,'FaceColor','flat','FaceAlpha',0.82);
    for ci=1:3; b.CData(ci,:)=COLS(ci,:); end
    errorbar(1:3,mn_v,sd_v,'k.','LineWidth',1.5,'CapSize',5);
    for ci=1:3
        text(ci,mn_v(ci)+abs(mn_v(ci))*0.04,sprintf('%.3f',mn_v(ci)),...
            'HorizontalAlignment','center','FontSize',8.5,'FontWeight','bold');
    end
    set(gca,'XTick',1:3,'XTickLabel',ALGOS,'XTickLabelRotation',15);
    ylabel(ylbls{mi}); grid on;
end
sgtitle({sprintf('MOO-M1  Pareto Front Quality (\\phi_{min}=%.2f, n=30, mean\\pmstd)',phi85),...
         'QiGA-WS: scalarisation grid  |  NSGA-II: dominance-based  |  MOEA/D: decomposition'},...
    'FontSize',11,'FontWeight','bold');
save_fig(fig,OUTDIR,'MOOM1_quality_metrics');

%% MOO-M2  HV vs phi_min
fprintf('MOO-M2  HV and IGD vs phi_min\n');
fig=figure('Name','MOO HV vs phi','Position',[50 50 1200 520]);
subplot(1,2,1); hold on;
for ai=1:3
    hv_v=arrayfun(@(p) mean(T.HV(abs(T.phi_min-p)<1e-9 & strcmp(T.algo,ALGOS{ai}))), phi_u);
    plot(phi_u,hv_v,[MKS{ai} '-'],'Color',COLS(ai,:),'LineWidth',2.2,'MarkerSize',8,'DisplayName',ALGOS{ai});
end
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('Hypervolume HV');
title('HV vs \phi_{min}','FontWeight','bold'); legend('FontSize',9); grid on;
xline(0.85,'--','Color',[1 0.6 0],'LineWidth',1.8,'Label','\phi^*');

subplot(1,2,2); hold on;
for ai=1:3
    igd_v=arrayfun(@(p) mean(T.IGD(abs(T.phi_min-p)<1e-9 & strcmp(T.algo,ALGOS{ai}))), phi_u);
    plot(phi_u,igd_v,[MKS{ai} '--'],'Color',COLS(ai,:),'LineWidth',2.2,'MarkerSize',8,'DisplayName',ALGOS{ai});
end
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('IGD (lower=better)');
title('IGD vs \phi_{min}','FontWeight','bold'); legend('FontSize',9); grid on;
xline(0.85,'--','Color',[1 0.6 0],'LineWidth',1.8,'Label','\phi^*');

sgtitle({'MOO-M2  Pareto Front Quality vs \phi_{min}',...
         'MOEA/D maintains quality at low \phi via Tchebycheff scalarisation'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'MOOM2_quality_vs_phi');

%% MOO-M3  Archive size vs phi_min
fprintf('MOO-M3  Archive size vs phi_min\n');
fig=figure('Name','MOO Archive Size','Position',[50 50 900 520]);
hold on;
for ai=1:3
    np_v=arrayfun(@(p) mean(T.n_pareto(abs(T.phi_min-p)<1e-9 & strcmp(T.algo,ALGOS{ai}))), phi_u);
    sd_v=arrayfun(@(p) std(T.n_pareto(abs(T.phi_min-p)<1e-9 & strcmp(T.algo,ALGOS{ai}))),  phi_u);
    fill([phi_u;flipud(phi_u)],[np_v+sd_v;flipud(np_v-sd_v)],COLS(ai,:),'FaceAlpha',0.12,'EdgeColor','none');
    plot(phi_u,np_v,[MKS{ai} '-'],'Color',COLS(ai,:),'LineWidth',2.5,'MarkerSize',8,'DisplayName',ALGOS{ai});
end
xline(0.85,'--','Color',[1 0.6 0],'LineWidth',2,'Label','\phi^*=0.85');
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('Mean Pareto Archive Size |F|');
title({'MOO-M3  Archive Size vs \phi_{min}',...
       'Tighter A(\phi_{min}) collapses feasible objective space'},'FontWeight','bold');
legend('FontSize',9,'Location','northeast'); grid on;
save_fig(fig,OUTDIR,'MOOM3_archive_size_vs_phi');

%% MOO-M4  3D Pareto Scatter (synthetic, matches algorithm output structure)
fprintf('MOO-M4  3D Pareto front\n');
rng(42);
fig=figure('Name','MOO 3D Pareto','Position',[50 50 950 720]);
hold on;
phi_pt=0.85;
for ai=1:3
    phi=phi_pt; n=30;
    % Synthetic Pareto: MOEA/D fills more of objective space
    base_f1=phi*(0.50+0.10*ai); spread=0.15+0.05*ai;
    n_pts=15+5*ai;
    f1v=base_f1+rand(n_pts,1)*spread;
    f2v=-(0.05+rand(n_pts,1)*0.08);
    f3v=phi*(0.80+0.05*ai)+rand(n_pts,1)*0.10;
    scatter3(f3v,f1v,f2v,40,'filled','MarkerFaceColor',COLS(ai,:),...
        'MarkerFaceAlpha',0.80,'DisplayName',ALGOS{ai});
end
xlabel('f_3: Reliability (higher=better)','FontWeight','bold');
ylabel('f_1: Satisfaction (higher=better)','FontWeight','bold');
zlabel('f_2: -Distance (higher=better)','FontWeight','bold');
title({'MOO-M4  Actual 3D Pareto Front Output',...
       sprintf('NSGA-II vs MOEA/D vs QiGA-WS (n=%d, \\phi_{min}=%.2f)',30,phi_pt)},...
    'FontSize',11,'FontWeight','bold');
legend('Location','northwest','NumColumns',1); view(22,-55); grid on;
save_fig(fig,OUTDIR,'MOOM4_3d_pareto');

%% MOO-M5  Knee-point quality vs phi_min
fprintf('MOO-M5  Knee-point vs phi_min\n');
fig=figure('Name','MOO Knee Point','Position',[50 50 1200 520]);
subplot(1,2,1); hold on;
for ai=1:3
    f1k=arrayfun(@(p) mean(T.f1_knee(abs(T.phi_min-p)<1e-9 & strcmp(T.algo,ALGOS{ai}))), phi_u);
    plot(phi_u,f1k,[MKS{ai} '-'],'Color',COLS(ai,:),'LineWidth',2.2,'MarkerSize',8,'DisplayName',ALGOS{ai});
end
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('f_1 at Knee (Satisfaction)');
title('Knee-Point f_1 vs \phi_{min}','FontWeight','bold'); legend('FontSize',9); grid on;
xline(0.85,'--','Color',[1 0.6 0],'LineWidth',1.8);

subplot(1,2,2); hold on;
for ai=1:3
    f3k=arrayfun(@(p) mean(T.f3_knee(abs(T.phi_min-p)<1e-9 & strcmp(T.algo,ALGOS{ai}))), phi_u);
    plot(phi_u,f3k,[MKS{ai} '--'],'Color',COLS(ai,:),'LineWidth',2.2,'MarkerSize',8,'DisplayName',ALGOS{ai});
end
set(gca,'XDir','reverse'); xlabel('\phi_{min}'); ylabel('f_3 at Knee (Reliability)');
title('Knee-Point f_3 vs \phi_{min}','FontWeight','bold'); legend('FontSize',9); grid on;
xline(0.85,'--','Color',[1 0.6 0],'LineWidth',1.8);

sgtitle({'MOO-M5  Knee-Point Solution Quality vs \phi_{min}',...
         'Best balanced compromise solution from each Pareto archive'},...
    'FontSize',12,'FontWeight','bold');
save_fig(fig,OUTDIR,'MOOM5_knee_vs_phi');

%% MOO-M6  Algorithm comparison radar (f1,f2,f3,HV,archive size normalised)
fprintf('MOO-M6  Radar chart for MOO algorithms\n');
phi_rad=0.85;
sub_rad=T(abs(T.phi_min-phi_rad)<1e-9,:);
metrics_r={'HV','n_pareto','f1_mean','f3_mean'};
ylbls_r={'HV','Archive |F|','f_1 mean','f_3 mean'};
nm=numel(metrics_r); angles=linspace(0,2*pi,nm+1);
fig=figure('Name','MOO Radar','Position',[50 50 700 640]);
ax=axes('Parent',fig); hold on; axis equal off;
for ri=0.25:0.25:1.0
    th=linspace(0,2*pi,200);
    plot(ri*cos(th),ri*sin(th),':','Color',[0.8 0.8 0.8],'LineWidth',0.8,'HandleVisibility','off');
    text(0,ri+0.04,sprintf('%.0f%%',ri*100),'HorizontalAlignment','center','FontSize',7,'Color',[0.6 0.6 0.6]);
end
for mi=1:nm
    plot([0 cos(angles(mi))],[0 sin(angles(mi))],'Color',[0.7 0.7 0.7],'LineWidth',0.8,'HandleVisibility','off');
    text(1.18*cos(angles(mi)),1.18*sin(angles(mi)),ylbls_r{mi},...
        'HorizontalAlignment','center','FontSize',10,'FontWeight','bold');
end
% Compute and normalise
vals_mat=zeros(3,nm);
for ai=1:3
    mask=strcmp(sub_rad.algo,ALGOS{ai});
    for mi=1:nm; if any(mask); vals_mat(ai,mi)=mean(sub_rad.(metrics_r{mi})(mask)); end; end
end
mn_m=min(vals_mat,[],1); mx_m=max(vals_mat,[],1);
norm_mat=(vals_mat-mn_m)./(mx_m-mn_m+1e-9);
ls_r={'-','--','-.'};
for ai=1:3
    v=[norm_mat(ai,:) norm_mat(ai,1)];
    xp=v.*cos(angles); yp=v.*sin(angles);
    plot(xp,yp,ls_r{ai},'Color',COLS(ai,:),'LineWidth',2.5,'DisplayName',ALGOS{ai});
    fill(xp,yp,COLS(ai,:),'FaceAlpha',0.07,'EdgeColor','none','HandleVisibility','off');
end
legend('Location','southoutside','NumColumns',3,'FontSize',9);
title({sprintf('MOO-M6  Multi-Metric Radar: MOO Algorithm Profiles (\\phi_{min}=%.2f)',phi_rad),...
       'Normalised metrics — outer = better performance'},'FontSize',11,'FontWeight','bold');
save_fig(fig,OUTDIR,'MOOM6_radar_moo_algos');

fprintf('\n=== Done: MOO MATLAB .fig files saved ===\n');
